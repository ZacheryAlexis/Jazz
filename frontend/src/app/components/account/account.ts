import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-account',
  templateUrl: './account.html',
  styleUrls: ['./account.css'],
  standalone: true,
  imports: [CommonModule]
})
export class AccountComponent {
  qrDataUrl: string | null = null;
  secret: string | null = null;
  message = '';
  loading = false;

  constructor(private auth: AuthService) {}

  async setupMfa() {
    this.loading = true;
    this.message = '';
    this.qrDataUrl = null;
    this.secret = null;
    try {
      const resp: any = await this.auth.mfaSetup().toPromise();
      if (resp && resp.qrCode) {
        this.qrDataUrl = resp.qrCode;
        this.secret = resp.secret;
        this.message = 'Scan the QR code with an authenticator app, then verify below.';
      } else {
        this.message = 'Unexpected response from server';
      }
    } catch (err: any) {
      this.message = err?.error?.error || 'MFA setup failed';
    }
    this.loading = false;
  }

  async verifyMfa(tokenInput: HTMLInputElement) {
    const token = tokenInput.value?.trim();
    if (!token) {
      this.message = 'Enter the 6-digit code';
      return;
    }
    this.loading = true;
    this.message = '';
    try {
      const resp: any = await this.auth.mfaVerify(token).toPromise();
      if (resp && resp.success) {
        this.message = 'MFA enabled successfully';
        // clear secret/qr since it's now enabled
        this.qrDataUrl = null;
        this.secret = null;
      } else {
        this.message = 'Verification failed';
      }
    } catch (err: any) {
      this.message = err?.error?.error || 'MFA verify failed';
    }
    this.loading = false;
  }
}
