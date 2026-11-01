import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect } from 'vitest';
import { PillBadge } from '../common/PillBadge';
import { LandingPage } from '../../pages/LandingPage';
import { ReviewQueuePage } from '../../pages/workspace/ReviewQueuePage';
import { ApplicationDetailPage } from '../../pages/workspace/ApplicationDetailPage';
import { ThemeProvider } from '../../context/ThemeContext';

const renderWithRouter = (ui: React.ReactElement) => {
  return render(
    <ThemeProvider>
      <BrowserRouter>{ui}</BrowserRouter>
    </ThemeProvider>
  );
};

describe('Nirikshan Design System & Pages', () => {
  it('renders PillBadge with different variants', () => {
    const { rerender } = render(<PillBadge variant="critical">Critical</PillBadge>);
    expect(screen.getByText('Critical')).toBeInTheDocument();

    rerender(<PillBadge variant="verified">E5 Verified</PillBadge>);
    expect(screen.getByText('E5 Verified')).toBeInTheDocument();

    rerender(<PillBadge variant="warning">Under review</PillBadge>);
    expect(screen.getByText('Under review')).toBeInTheDocument();
  });

  it('renders Landing Page with floating navbar, hero, 3 stat cards, and magnifier document viewer', () => {
    renderWithRouter(<LandingPage />);

    // Headline (3 lines)
    const h1 = screen.getByRole('heading', { level: 1 });
    expect(h1).toHaveTextContent(/Every approval/i);
    expect(h1).toHaveTextContent(/checked against/i);
    expect(h1).toHaveTextContent(/its evidence/i);

    // Floating Navbar button
    expect(screen.getByRole('button', { name: /Open workspace/i })).toBeInTheDocument();

    // 3 Stat Cards
    expect(screen.getByText(/330 teachers/i)).toBeInTheDocument();
    expect(screen.getByText(/7 colleges/i)).toBeInTheDocument();
    expect(screen.getByText(/9.61 acres/i)).toBeInTheDocument();

    // Document Viewer and Revisions
    expect(screen.getAllByText(/Revision 1 · Signed/i)[0]).toBeInTheDocument();
    expect(screen.getByText(/Revision 2 · Form Changes/i)).toBeInTheDocument();
    expect(screen.getByText(/Revision 3 · Post-Sign Alteration/i)).toBeInTheDocument();

    // Mandatory Footer Disclaimer
    expect(
      screen.getByText(/Decision support only\. Findings are preliminary indicators for review\./i)
    ).toBeInTheDocument();
  });

  it('renders Review Queue page with 4 KPI cards and filter tabs', () => {
    renderWithRouter(<ReviewQueuePage />);

    // 4 KPI Cards
    expect(screen.getByText(/^Applications$/i)).toBeInTheDocument();
    expect(screen.getAllByText(/^Open Findings$/i)[0]).toBeInTheDocument();
    expect(screen.getByText(/^High or Critical$/i)).toBeInTheDocument();
    expect(screen.getByText(/^Awaiting Confirmation$/i)).toBeInTheDocument();

    // Filter tabs
    expect(screen.getByRole('button', { name: /Needs attention/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /All Applications/i })).toBeInTheDocument();

    // Institutions table
    expect(screen.getAllByText(/Apex Institute of Technology & Management/i)[0]).toBeInTheDocument();
    expect(screen.getByText(/Linked Applications Graph/i)).toBeInTheDocument();
  });

  it('renders Application Detail page with 5 tabs and Proof Strength grid', () => {
    renderWithRouter(<ApplicationDetailPage />);

    // Header items
    expect(
      screen.getByRole('heading', { name: /Apex Institute of Technology & Management/i })
    ).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Ask why/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Decide/i })).toBeInTheDocument();

    // Tabs
    expect(screen.getByRole('button', { name: /Summary/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Findings/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Documents/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Comparisons/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Activity/i })).toBeInTheDocument();

    // Proof strength grid in Summary
    expect(screen.getByText(/Proof Strength Grid/i)).toBeInTheDocument();
    expect(screen.getByText(/Faculty:Student Ratio/i)).toBeInTheDocument();
    expect(screen.getByText(/Land Title & 30-Year/i)).toBeInTheDocument();
  });
});
