import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import ProgressBar from '../../src/components/ProgressBar';

describe('ProgressBar', () => {
  it('shows the message and the rounded percentage', () => {
    render(<ProgressBar progress={42.4} message="Cleaning data" />);

    expect(screen.getByText('Cleaning data')).toBeInTheDocument();
    expect(screen.getByText('42%')).toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '42');
  });

  it('hides the percentage when showPercentage is false', () => {
    render(<ProgressBar progress={42} message="Training" showPercentage={false} />);

    expect(screen.getByText('Training')).toBeInTheDocument();
    expect(screen.queryByText('42%')).not.toBeInTheDocument();
  });
});
