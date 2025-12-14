import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  // Build API URL from the host serving the frontend so requests target the VM backend
  private apiUrl = `http://${window.location.hostname}:3000/api`;

  constructor(private http: HttpClient) { }

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
