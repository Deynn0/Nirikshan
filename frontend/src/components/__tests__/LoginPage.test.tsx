import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { LoginPage } from '../../pages/LoginPage';
import { AuthProvider } from '../../context/AuthContext';

describe('LoginPage Component', () => {
  it('renders Nirikshan (निरीक्षण) branding and role selector', () => {
    render(
      <AuthProvider>
        <BrowserRouter>
          <LoginPage />
        </BrowserRouter>
      </AuthProvider>
    );

    expect(screen.getByText(/Nirikshan/i)).toBeInTheDocument();
    expect(screen.getByText(/\(निरीक्षण\)/i)).toBeInTheDocument();
    expect(screen.getByText(/AICTE Scrutiny Officer/i)).toBeInTheDocument();
    expect(screen.getByText(/Applicant \(Institution Registrar\)/i)).toBeInTheDocument();
  });

  it('allows clicking quick demo login buttons', () => {
    render(
      <AuthProvider>
        <BrowserRouter>
          <LoginPage />
        </BrowserRouter>
      </AuthProvider>
    );

    const officerDemoBtn = screen.getByText('AICTE Officer');
    expect(officerDemoBtn).toBeInTheDocument();
    fireEvent.click(officerDemoBtn);
  });
});
