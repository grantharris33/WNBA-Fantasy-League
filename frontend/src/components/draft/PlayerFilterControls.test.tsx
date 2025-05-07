import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import PlayerFilterControls from './PlayerFilterControls';

// Mock lodash debounce to make it immediate for testing
// jest.mock('lodash', () => ({
//   ...jest.requireActual('lodash'),
//   debounce: (fn: (...args: any[]) => void) => fn, // Make debounce call the function immediately
// }));

// More specific mock for lodash, especially if only debounce is used by the component
jest.mock('lodash', () => {
  const originalLodash = jest.requireActual('lodash');
  return {
    __esModule: true, // This is important for modules with default exports or mixed exports
    ...originalLodash,
    debounce: (fn: (...args: unknown[]) => void) => {
      // Return a function that behaves like the original debounced function but calls immediately
      // This is a simplified immediate mock. For more complex scenarios, you might need to manage timers.
      return (...args: unknown[]) => fn(...args);
    },
  };
});

describe('PlayerFilterControls', () => {
  const mockOnFilterChange = jest.fn();
  const availablePositions = ['G', 'F', 'C'];

  beforeEach(() => {
    mockOnFilterChange.mockClear();
  });

  it('renders input fields and dropdown', () => {
    render(<PlayerFilterControls onFilterChange={mockOnFilterChange} availablePositions={availablePositions} />);
    expect(screen.getByPlaceholderText('Search player by name...')).toBeInTheDocument();
    expect(screen.getByRole('combobox')).toBeInTheDocument();
    expect(screen.getByText('All Positions')).toBeInTheDocument();
    availablePositions.forEach(pos => {
      expect(screen.getByText(pos)).toBeInTheDocument();
    });
  });

  it('calls onFilterChange with name when name input changes', async () => {
    render(<PlayerFilterControls onFilterChange={mockOnFilterChange} availablePositions={availablePositions} />);
    const nameInput = screen.getByPlaceholderText('Search player by name...');
    fireEvent.change(nameInput, { target: { value: 'Test Player' } });

    await waitFor(() => {
        expect(mockOnFilterChange).toHaveBeenCalledWith({ name: 'Test Player', position: '' });
    });
  });

  it('calls onFilterChange with position when position select changes', async () => {
    render(<PlayerFilterControls onFilterChange={mockOnFilterChange} availablePositions={availablePositions} />);
    const positionSelect = screen.getByRole('combobox');
    fireEvent.change(positionSelect, { target: { value: 'G' } });

    await waitFor(() => {
        expect(mockOnFilterChange).toHaveBeenCalledWith({ name: '', position: 'G' });
    });
  });

  it('calls onFilterChange with both name and position after interactions', async () => {
    render(<PlayerFilterControls onFilterChange={mockOnFilterChange} availablePositions={availablePositions} />);
    const nameInput = screen.getByPlaceholderText('Search player by name...');
    const positionSelect = screen.getByRole('combobox');

    fireEvent.change(nameInput, { target: { value: 'Guardia' } });
    // Due to mocked debounce being immediate, this call will happen with { name: 'Guardia', position: '' }

    fireEvent.change(positionSelect, { target: { value: 'F' } });
    // This call will happen with { name: 'Guardia' (from previous state), position: 'F' }

    await waitFor(() => {
        // The PlayerFilterControls component calls debouncedFilterChange in a useEffect hook
        // that depends on [nameSearch, selectedPosition].
        // When name is typed, it calls with (name, '').
        // When position is selected, it calls with (name, position).
        expect(mockOnFilterChange).toHaveBeenCalledTimes(2); // Once for name, once for position with updated name
        expect(mockOnFilterChange).toHaveBeenCalledWith({ name: 'Guardia', position: '' });
        expect(mockOnFilterChange).toHaveBeenLastCalledWith({ name: 'Guardia', position: 'F' });
    });
  });
});