// Jazz MEAN Stack Frontend - Angular Component: Login Page
// This is the main login component for the Jazz web interface

import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-login',
  templateUrl: './login.html',
  styleUrls: ['./login.css'],
  imports: [CommonModule, FormsModule],
  standalone: true
})
export class LoginComponent {
  username = '';
  password = '';
  email = '';
  isRegistering = false;
  error = '';
  loading = false;
  // MFA state
  mfaStage = false;
  mfaToken = '';
  mfaUserId: string | null = null;

  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  toggleMode() {
    this.isRegistering = !this.isRegistering;
    this.error = '';
    this.username = '';
    this.password = '';
    this.email = '';
  }

  onLogin() {
    if (!this.username || !this.password) {
      this.error = 'Please fill in all fields';
      return;
    }

    this.loading = true;
    this.authService.login(this.username, this.password).subscribe(
      (response: any) => {
        // If server indicates MFA is required, prompt for MFA token
        if (response && response.mfaRequired) {
          this.mfaStage = true;
          this.mfaUserId = response.userId;
          this.loading = false;
          return;
        }

        // Save token, username and MFA flag
        localStorage.setItem('token', response.token);
        localStorage.setItem('username', response.user.username);
        try {
          const mfaFlag = !!(response.user && response.user.mfaEnabled);
          localStorage.setItem('mfaEnabled', mfaFlag ? '1' : '0');
        } catch (e) { localStorage.setItem('mfaEnabled', '0'); }

        // Navigate to chat. Banner in chat will prompt for MFA setup when needed.
        this.router.navigate(['/chat']);
      },
      (error: any) => {
        this.error = error.error?.error || 'Login failed';
        this.loading = false;
      }
    );
  }

  async onMfaSubmit() {
    if (!this.mfaUserId || !this.mfaToken) {
      this.error = 'Enter MFA token';
      return;
    }

    this.loading = true;
    this.authService.mfaLogin(this.mfaUserId, this.mfaToken).subscribe(
      (resp: any) => {
        localStorage.setItem('token', resp.token);
        localStorage.setItem('username', resp.user.username);
        this.router.navigate(['/chat']);
      },
      (err: any) => {
        this.error = err.error?.error || 'MFA verification failed';
        this.loading = false;
      }
    );
  }

  onRegister() {
    if (!this.username || !this.email || !this.password) {
      this.error = 'Please fill in all fields';
      return;
    }

    this.loading = true;
    this.authService.register(this.username, this.email, this.password).subscribe(
      (response: any) => {
        localStorage.setItem('token', response.token);
        localStorage.setItem('username', response.user.username);
        try {
          const mfaFlag = !!(response.user && response.user.mfaEnabled);
          localStorage.setItem('mfaEnabled', mfaFlag ? '1' : '0');
        } catch (e) { localStorage.setItem('mfaEnabled', '0'); }

        // Navigate to chat; the banner will prompt for MFA setup where appropriate.
        this.router.navigate(['/chat']);
      },
      (error: any) => {
        this.error = error.error?.error || 'Registration failed';
        this.loading = false;
      }
    );
  }
}
