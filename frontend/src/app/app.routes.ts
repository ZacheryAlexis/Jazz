import { Routes } from '@angular/router';
import { LoginComponent } from './components/login/login';
import { ChatComponent } from './components/chat/chat';

export const routes: Routes = [
  { path: '', redirectTo: '/login', pathMatch: 'full' },
  { path: 'login', component: LoginComponent },
  { path: 'chat', component: ChatComponent }
];
