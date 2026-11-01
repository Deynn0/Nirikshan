import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { TrustLadderBadge } from '../TrustLadderBadge';

describe('TrustLadderBadge Component', () => {
  it('renders Level 1 Cryptographic Proof correctly', () => {
    render(<TrustLadderBadge level="CRYPTOGRAPHIC_PROOF" />);
    expect(screen.getByText(/Level 1: Cryptographic Proof/i)).toBeInTheDocument();
  });

  it('renders Level 2 Statutory Database correctly', () => {
    render(<TrustLadderBadge level="STATUTORY_DATABASE" />);
    expect(screen.getByText(/Level 2: Statutory Database/i)).toBeInTheDocument();
  });

  it('renders Level 3 Hardened Document correctly', () => {
    render(<TrustLadderBadge level="HARDENED_DOCUMENT" />);
    expect(screen.getByText(/Level 3: Hardened Document Forensics/i)).toBeInTheDocument();
  });

  it('always displays the mandatory Advisory badge for Level 4 Model Predictions', () => {
    render(<TrustLadderBadge level="MODEL_PREDICTION" isModelAdvisory={true} />);
    expect(screen.getByText(/Level 4: Model Prediction/i)).toBeInTheDocument();
    const advisoryBadge = screen.getByText('Advisory');
    expect(advisoryBadge).toBeInTheDocument();
  });

  it('renders Level 5 Unverified Claim correctly', () => {
    render(<TrustLadderBadge level="UNVERIFIED_CLAIM" />);
    expect(screen.getByText(/Level 5: Unverified Claim/i)).toBeInTheDocument();
  });
});
