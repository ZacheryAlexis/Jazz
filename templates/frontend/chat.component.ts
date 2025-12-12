// Jazz MEAN Stack Frontend - Chat Component TypeScript
// This component handles the chat interface and communication with the backend

import { Component, OnInit } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Router } from '@angular/router';

interface ChatMessage {
  type: 'user' | 'assistant';
  text: string;
  timestamp?: Date;
}

@Component({
  selector: 'app-chat',
  templateUrl: './chat.component.html',
  styleUrls: ['./chat.component.css']
})
export class ChatComponent implements OnInit {
  messages: ChatMessage[] = [];
  userMessage = '';
  username = '';
  loading = false;
  error = '';

  private apiUrl = 'http://localhost:3000/api/chat';
  private historyUrl = 'http://localhost:3000/api/chat/history';

  constructor(private http: HttpClient, private router: Router) {}

  ngOnInit() {
    // Get logged-in username from localStorage
    const storedUsername = localStorage.getItem('username');
    const token = localStorage.getItem('token');

    if (!token) {
      // Not logged in, redirect to login
      this.router.navigate(['/login']);
      return;
    }

    this.username = storedUsername || 'User';

    // Load chat history
    this.loadChatHistory();
  }

  loadChatHistory() {
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

  sendMessage() {
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

    const token = localStorage.getItem('token');
    const headers = new HttpHeaders({
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    });

    this.http.post<any>(
      this.apiUrl,
      { message: messageToSend },
      { headers }
    ).subscribe(
      (response) => {
        if (response.success) {
          // Add assistant response
          this.messages.push({
            type: 'assistant',
            text: response.assistantResponse,
            timestamp: response.timestamp ? new Date(response.timestamp) : new Date()
          });
        }
        this.loading = false;
      },
      (error) => {
        this.error = error.error?.error || 'Failed to get response from assistant';
        
        // Show error as assistant message
        this.messages.push({
          type: 'assistant',
          text: `Error: ${this.error}`,
          timestamp: new Date()
        });
        
        this.loading = false;
      }
    );
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
    const messagesDiv = document.querySelector('.chat-messages');
    if (messagesDiv) {
      messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }
  }
}
