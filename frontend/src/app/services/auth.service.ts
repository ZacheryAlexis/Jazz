import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  // Default API URL (used on server) and updated in constructor when running in browser
  private apiUrl = 'http://localhost:3000/api';

  constructor(private http: HttpClient) {
    if (typeof window !== 'undefined' && (window as any).location && (window as any).location.hostname) {
      this.apiUrl = `http://${(window as any).location.hostname}:3000/api`;
    }
  }

  register(username: string, email: string, password: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/auth/register`, {
      username,
      email,
      password
    });
  }

  login(username: string, password: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/auth/login`, {
      username,
      password
    });
  }

  // Perform MFA login using the temporary userId returned when MFA is required
  mfaLogin(userId: string, token: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/mfa/login`, {
      userId,
      token
    });
  }

  // (Optional) Setup MFA for the current authenticated user
  mfaSetup(): Observable<any> {
    return this.http.post(`${this.apiUrl}/mfa/setup`, {}, { headers: { 'Authorization': `Bearer ${this.getToken()}` } });
  }

  // (Optional) Verify MFA setup token and enable MFA
  mfaVerify(token: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/mfa/verify`, { token }, { headers: { 'Authorization': `Bearer ${this.getToken()}` } });
  }

  getToken(): string | null {
    return localStorage.getItem('token');
  }

  isLoggedIn(): boolean {
    return !!this.getToken();
  }

  logout(): void {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
  }
}
