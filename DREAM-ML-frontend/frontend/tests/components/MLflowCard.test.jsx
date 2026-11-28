import { afterEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import axios from '../../src/utils/axiosConfig';
import { AppContext } from '../../src/AppContext';
import MLflowCard from '../../src/components/MLflowCard';

vi.mock('../../src/utils/axiosConfig', () => ({
  default: { post: vi.fn() },
}));

function renderCard() {
  const context = {
    mlflowStartingInProgress: false,
    setMlflowStartingInProgress: vi.fn(),
  };
  return render(
    <AppContext.Provider value={context}>
      <MLflowCard />
    </AppContext.Provider>,
  );
}

describe('MLflowCard', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('opens MLflow in a new tab without access to this window', async () => {
    axios.post.mockResolvedValue({ data: {} });
    const open = vi.spyOn(window, 'open').mockReturnValue(null);
    renderCard();

    fireEvent.click(screen.getByRole('button', { name: 'Iniciar MLflow' }));

    await waitFor(() => expect(open).toHaveBeenCalledTimes(1));
    const [url, target, features] = open.mock.calls[0];
    expect(url).toBe('http://127.0.0.1:5000/');
    expect(target).toBe('_blank');
    expect(features.split(',')).toContain('noopener');
  });

  it('does not open MLflow when the server fails to start', async () => {
    axios.post.mockRejectedValue({ response: { data: { status: 'Error' } } });
    const open = vi.spyOn(window, 'open').mockReturnValue(null);
    renderCard();

    fireEvent.click(screen.getByRole('button', { name: 'Iniciar MLflow' }));

    expect(await screen.findAllByText('Error')).not.toHaveLength(0);
    expect(open).not.toHaveBeenCalled();
  });
});
