import React from 'react';
import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { LoginPage } from '../../pages/LoginPage';
import { AuthProvider } from '../../context/AuthContext';
import { ThemeProvider } from '../../context/ThemeContext';

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

describe('LoginPage Component', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('renders Pramana workspace and sign in to review headline', () => {
    const qc = createTestQueryClient();
    render(
      <QueryClientProvider client={qc}>
        <ThemeProvider>
          <AuthProvider>
            <BrowserRouter>
              <LoginPage />
            </BrowserRouter>
          </AuthProvider>
        </ThemeProvider>
      </QueryClientProvider>
    );

    expect(screen.getByText(/Pramana workspace/i)).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /Sign in to review/i })).toBeInTheDocument();
    expect(screen.getByText(/Demo accounts \(synthetic data\)/i)).toBeInTheDocument();
  });

  it('renders username and password inputs and allows typing', () => {
    const qc = createTestQueryClient();
    render(
      <QueryClientProvider client={qc}>
        <ThemeProvider>
          <AuthProvider>
            <BrowserRouter>
              <LoginPage />
            </BrowserRouter>
          </AuthProvider>
        </ThemeProvider>
      </QueryClientProvider>
    );

    const usernameInput = screen.getByPlaceholderText('officer');
    expect(usernameInput).toBeInTheDocument();
    fireEvent.change(usernameInput, { target: { value: 'officer.test' } });
    expect(usernameInput).toHaveValue('officer.test');
  });

  it('displays demo accounts for officials and institutions', async () => {
    const qc = createTestQueryClient();
    render(
      <QueryClientProvider client={qc}>
        <ThemeProvider>
          <AuthProvider>
            <BrowserRouter>
              <LoginPage />
            </BrowserRouter>
          </AuthProvider>
        </ThemeProvider>
      </QueryClientProvider>
    );

    // Wait for the demo account cards to load from api.demoAccounts
    const officerCard = await screen.findByText(/Dr. Arvind Sharma/i);
    expect(officerCard).toBeInTheDocument();
    expect(screen.getByText(/IIT Delhi/i)).toBeInTheDocument();
  });
});
