// Jazz MEAN Stack Frontend - Chat Component TypeScript
// This component handles the chat interface and communication with the backend

import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Router } from '@angular/router';

interface ChatMessage {
  type: 'user' | 'assistant';
  text: string;
  timestamp?: Date;
  fullResponse?: string; // optional full response metadata
}

@Component({
  selector: 'app-chat',
  templateUrl: './chat.html',
  styleUrls: ['./chat.css'],
  imports: [CommonModule, FormsModule],
  standalone: true
})
export class ChatComponent implements OnInit {
  messages: ChatMessage[] = [];
  userMessage = '';
  username = '';
  loading = false;
  error = '';
  elapsedSeconds = 0;
  private elapsedInterval: any = null;
  private currentAbortController: AbortController | null = null;
  private pollIntervalId: any = null;
  private currentEventSource: any = null;
  // Modal state for showing full LLM output
  modalOpen = false;
  modalContent = '';

  // Default API URLs (safe for server-side build). They will be updated
  // at runtime in the constructor when `window` is available.
  private apiUrl = 'http://localhost:3000/api/chat';
  private historyUrl = 'http://localhost:3000/api/chat/history';

  constructor(private http: HttpClient, private router: Router) {
    if (typeof window !== 'undefined' && (window as any).location && (window as any).location.hostname) {
      this.apiUrl = `http://${(window as any).location.hostname}:3000/api/chat`;
      this.historyUrl = `http://${(window as any).location.hostname}:3000/api/chat/history`;
    }
  }

  showFull(message: ChatMessage) {
    if (!message.fullResponse) return;
    // Show full response in modal
    this.modalContent = message.fullResponse;
    this.modalOpen = true;
  }

  closeModal() {
    this.modalOpen = false;
    this.modalContent = '';
  }

  ngOnInit() {
    // Get logged-in username from localStorage (only when running in browser)
    const token = (typeof window !== 'undefined') ? localStorage.getItem('token') : null;
    const storedUsername = (typeof window !== 'undefined') ? localStorage.getItem('username') : null;

    if (!token) {
      // Not logged in: only redirect when running in browser (avoid redirect during server build)
      if (typeof window !== 'undefined') {
        this.router.navigate(['/login']);
        return;
      }
    }

    this.username = storedUsername || 'User';

    // Load chat history (only in browser/runtime)
    if (typeof window !== 'undefined' && token) {
      this.loadChatHistory();
    }
  }

  loadChatHistory() {
    if (typeof window === 'undefined') return;

    const token = localStorage.getItem('token');
    const headers = new HttpHeaders({
      'Authorization': `Bearer ${token}`
    });

    this.http.get<any>(this.historyUrl, { headers }).subscribe(
      (response) => {
        if (response.success && response.history) {
          // Reverse so oldest messages are first
          this.messages = response.history.reverse().map((log: any) => [
            { type: 'user' as const, text: log.userMessage },
            { type: 'assistant' as const, text: log.assistantResponse }
          ]).flat();
        }
      },
      (error) => {
        // Silently fail - it's okay if history is empty
        console.log('Chat history empty or error:', error);
      }
    );
  }

  async sendMessage(): Promise<void> {
    if (!this.userMessage.trim()) {
      return;
    }

    const messageToSend = this.userMessage;
    this.userMessage = '';
    this.loading = true;
    this.error = '';

    // Add user message to display immediately
    this.messages.push({
      type: 'user',
      text: messageToSend,
      timestamp: new Date()
    });

    // Debug: log outgoing message
    console.log('[Chat] Sending message:', messageToSend);

    const token = (typeof window !== 'undefined') ? localStorage.getItem('token') : '';

    // Heuristic: detect score queries and try fast live-score path first
    const isScoreQuery = /who(?:'|)s?\s+winning|who\s+win|score|what\s+is\s+the\s+score/i.test(messageToSend);
    if (isScoreQuery) {
      try {
        const liveResp = await fetch(`http://${(window as any).location.hostname}:3000/api/live_score?q=${encodeURIComponent(messageToSend)}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (liveResp.ok) {
          const jr = await liveResp.json();
          if (jr && jr.success && jr.text) {
            this.messages.push({ type: 'assistant', text: jr.text, timestamp: new Date() });
            this.loading = false;
            if (this.elapsedInterval) { clearInterval(this.elapsedInterval); this.elapsedInterval = null; }
            return;
          }
        }
      } catch (e) {
        // ignore live score failures and fall back to streaming
        console.log('Live score lookup failed, falling back to LLM:', e);
      }
    }

    // Start streaming via SSE
    this.elapsedSeconds = 0;
    this.elapsedInterval = setInterval(() => this.elapsedSeconds++, 1000);

    try {
      // Request a short-lived stream token from backend for SSE
      let streamToken = null;
      try {
        const resp = await fetch(`http://${(window as any).location.hostname}:3000/api/stream_token`, { method: 'POST', headers: { 'Authorization': `Bearer ${token}` } });
        if (resp.ok) {
          const jr = await resp.json();
          if (jr && jr.success && jr.token) streamToken = jr.token;
        }
      } catch (e) {
        console.warn('Failed to get stream token, falling back to JWT in query:', e);
      }

      const tokenToUse = streamToken || token || '';
      const esUrl = `http://${(window as any).location.hostname}:3000/api/chat/stream?token=${encodeURIComponent(tokenToUse)}&message=${encodeURIComponent(messageToSend)}`;
      const es = new EventSource(esUrl);
      this.currentEventSource = es;

      // Create an assistant placeholder message we will append to
      const assistantMsg: ChatMessage = { type: 'assistant', text: '', timestamp: new Date() };
      this.messages.push(assistantMsg);

      // Handle primary concise data (first data event contains parsed response)
      es.onmessage = (ev: MessageEvent) => {
        const chunk = ev.data;
        assistantMsg.text = (assistantMsg.text + (assistantMsg.text ? ' ' : '') + chunk).trim();
        // As soon as we receive the first concise answer chunk, stop showing the global loading UI
        if (this.loading) {
          this.loading = false;
          if (this.elapsedInterval) { clearInterval(this.elapsedInterval); this.elapsedInterval = null; }
          if (this.pollIntervalId) { clearInterval(this.pollIntervalId); this.pollIntervalId = null; }
          // Keep the EventSource open to receive `detail` events, but UI is now showing the answer
        }
      };

      // Meta event contains model/duration info
      es.addEventListener('meta', (ev: any) => {
        try {
          const meta = JSON.parse(ev.data);
          // Append a short meta suffix to the assistant message (optional)
            if (meta && (meta.model || meta.duration_ms || meta.full_response)) {
            const model = meta.model ? `${meta.model}` : '';
            const dur = meta.duration_ms ? `${Math.round(meta.duration_ms)}ms` : '';
            const suffix = ` (${[model, dur].filter(Boolean).join(' • ')})`;
            assistantMsg.text = (assistantMsg.text + suffix).trim();
            if (meta.full_response) {
              assistantMsg.fullResponse = meta.full_response;
            }
          }
        } catch (e) {
          console.log('Invalid meta from stream', ev.data);
        }
      });

      // Detail events are further streaming output after the concise answer
      es.addEventListener('detail', (ev: any) => {
        assistantMsg.text = (assistantMsg.text + ' ' + ev.data).trim();
      });

      es.addEventListener('stderr', (ev: any) => {
        console.warn('Stream stderr:', ev.data);
      });

      es.addEventListener('done', (ev: any) => {
        try { const info = JSON.parse(ev.data); console.log('Stream done', info); } catch(e){}
        // Close and cleanup
        try { es.close(); } catch (e) {}
        this.currentEventSource = null;
        this.loading = false;
        if (this.elapsedInterval) { clearInterval(this.elapsedInterval); this.elapsedInterval = null; }
        if (this.pollIntervalId) { clearInterval(this.pollIntervalId); this.pollIntervalId = null; }
      });

      // Fallback polling to pick up DB-saved response if needed
      this.pollIntervalId = setInterval(() => this.checkHistoryForResponse(messageToSend), 2000);

    } catch (err) {
      console.error('Streaming error, falling back to POST:', err);
      // Fall back to original POST behavior
      try {
        const resp = await fetch(this.apiUrl, {
          method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` }, body: JSON.stringify({ message: messageToSend })
        });
        const response = await resp.json();
        if (response && response.success) {
          this.messages.push({ type: 'assistant', text: response.assistantResponse, timestamp: new Date() });
        } else {
          this.messages.push({ type: 'assistant', text: `Error: ${response?.error || 'No response'}`, timestamp: new Date() });
        }
      } catch (e: any) {
        this.messages.push({ type: 'assistant', text: `Error: ${e?.message || String(e)}`, timestamp: new Date() });
      } finally {
        this.loading = false;
        if (this.elapsedInterval) { clearInterval(this.elapsedInterval); this.elapsedInterval = null; }
      }
    }
  }

  cancelRequest() {
    // If streaming via EventSource, close it to trigger backend abort
    if (this.currentEventSource) {
      try { this.currentEventSource.close(); } catch (e) {}
      this.currentEventSource = null;
    }

    if (this.currentAbortController) {
      try { this.currentAbortController.abort(); } catch (e) {}
      this.currentAbortController = null;
    }

    this.loading = false;
    if (this.elapsedInterval) { clearInterval(this.elapsedInterval); this.elapsedInterval = null; }
    if (this.pollIntervalId) { clearInterval(this.pollIntervalId); this.pollIntervalId = null; }
    this.elapsedSeconds = 0;
  }

  // Poll chat history to find the assistant response saved by the backend
  private async checkHistoryForResponse(originalUserMessage: string) {
    if (typeof window === 'undefined') return;
    try {
      const token = localStorage.getItem('token');
      const resp = await fetch(this.historyUrl, { headers: { 'Authorization': `Bearer ${token}` } });
      if (!resp.ok) return;
      const data = await resp.json();
      if (!data || !data.history) return;

      // Find a history entry matching the user message (most recent first)
      for (const log of data.history) {
        if (!log.userMessage) continue;
        if (log.userMessage.trim() === originalUserMessage.trim() && log.assistantResponse) {
          // Avoid duplicate assistant messages
          const already = this.messages.some(m => m.type === 'assistant' && m.text === log.assistantResponse);
          if (!already) {
            this.messages.push({ type: 'assistant', text: log.assistantResponse, timestamp: log.timestamp ? new Date(log.timestamp) : new Date() });
          }
          if (this.pollIntervalId) { clearInterval(this.pollIntervalId); this.pollIntervalId = null; }
          // stop elapsed timer
          if (this.elapsedInterval) { clearInterval(this.elapsedInterval); this.elapsedInterval = null; }
          this.loading = false;
          this.elapsedSeconds = 0;
          return;
        }
      }
    } catch (e) {
      // ignore polling errors
    }
  }

  clearHistory() {
    if (confirm('Are you sure you want to clear chat history? This cannot be undone.')) {
      this.messages = [];
      // Note: You may want to add a backend endpoint to delete chat logs
    }
  }

  logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    this.router.navigate(['/login']);
  }

  // Handle Enter key to send message
  onKeyPress(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }

  // Scroll to bottom when messages change
  ngAfterViewChecked() {
    if (typeof document !== 'undefined') {
      const messagesDiv = document.querySelector('.chat-messages');
      if (messagesDiv) {
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
      }
    }
  }
}
