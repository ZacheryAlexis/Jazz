// Jazz MEAN Stack Frontend - Angular Component: Login Page
// This is the main login component for the Jazz web interface

import { Component } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent {
  username = '';
  password = '';
  email = '';
  isRegistering = false;
  error = '';
  loading = false;

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
        localStorage.setItem('token', response.token);
        localStorage.setItem('username', response.user.username);
        this.router.navigate(['/chat']);
      },
      (error: any) => {
        this.error = error.error?.error || 'Login failed';
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
        this.router.navigate(['/chat']);
      },
      (error: any) => {
        this.error = error.error?.error || 'Registration failed';
        this.loading = false;
      }
    );
  }
}
