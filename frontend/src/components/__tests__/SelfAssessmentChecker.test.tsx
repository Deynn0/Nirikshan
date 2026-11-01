import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { SelfAssessmentChecker } from '../applicant/SelfAssessmentChecker';

describe('SelfAssessmentChecker Component', () => {
  it('renders pre-submission readiness check and all 5 statutory rules', () => {
    render(<SelfAssessmentChecker />);

    expect(screen.getByText(/Self-Assessment Readiness Check/i)).toBeInTheDocument();
    expect(screen.getByText(/Pre-Submission Audit/i)).toBeInTheDocument();
    expect(screen.getByText(/Minimum Campus Land Area/i)).toBeInTheDocument();
    expect(screen.getByText(/Student-to-Faculty Ratio/i)).toBeInTheDocument();
    expect(screen.getByText(/Cadre Distribution Ratio/i)).toBeInTheDocument();
    expect(screen.getByText(/Joint Security Deposit FDR/i)).toBeInTheDocument();
    expect(screen.getByText(/Total Built-up Instructional Area/i)).toBeInTheDocument();
  });

  it('correctly calculates pass when land area exceeds rural requirement (>= 5.0 acres)', () => {
    render(
      <SelfAssessmentChecker
        initialValues={{
          locationType: 'RURAL',
          landAreaAcres: 6.0,
        }}
      />
    );

    // Minimum Land rule should show PASS
    const landRule = screen.getByText(/Minimum Campus Land Area/i).closest('div');
    expect(landRule).toBeInTheDocument();
    expect(screen.getByText(/Compliant. Your land parcel exceeds/i)).toBeInTheDocument();
  });

  it('triggers deficiency warning or failure when professors count is 0', () => {
    render(
      <SelfAssessmentChecker
        initialValues={{
          professors: 0,
          assocProfessors: 4,
          asstProfessors: 14,
        }}
      />
    );

    expect(screen.getByText(/At least 1 full-time regular Professor with Ph.D. is mandatory/i)).toBeInTheDocument();
  });
});
