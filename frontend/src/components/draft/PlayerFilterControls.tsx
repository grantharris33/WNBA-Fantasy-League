import React, { useState, useEffect, useMemo } from 'react';
import { debounce } from 'lodash'; // For debouncing search input

interface PlayerFilterControlsProps {
  onFilterChange: (filters: { name: string; position: string }) => void;
  availablePositions: string[]; // e.g., ['G', 'F', 'C', 'F-C']
}

const PlayerFilterControls: React.FC<PlayerFilterControlsProps> = ({ onFilterChange, availablePositions }) => {
  const [nameSearch, setNameSearch] = useState('');
  const [selectedPosition, setSelectedPosition] = useState(''); // '' for all positions

  const debouncedFilterChange = useMemo(
    () => debounce(onFilterChange, 300),
    [onFilterChange]
  );

  useEffect(() => {
    debouncedFilterChange({ name: nameSearch, position: selectedPosition });
    // Cleanup debounce on unmount
    return () => {
      debouncedFilterChange.cancel();
    };
  }, [nameSearch, selectedPosition, debouncedFilterChange]);

  const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setNameSearch(e.target.value);
  };

  const handlePositionChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedPosition(e.target.value);
  };

  return (
    <div className="p-4 bg-gray-50 rounded border mb-4 flex flex-col sm:flex-row gap-4 items-center">
      <div className="flex-grow w-full sm:w-auto">
        <label htmlFor="nameSearch" className="sr-only">Search by name</label>
        <input
          type="text"
          id="nameSearch"
          placeholder="Search player by name..."
          value={nameSearch}
          onChange={handleNameChange}
          className="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500"
        />
      </div>
      <div className="w-full sm:w-auto sm:min-w-[150px]">
        <label htmlFor="positionFilter" className="sr-only">Filter by position</label>
        <select
          id="positionFilter"
          value={selectedPosition}
          onChange={handlePositionChange}
          className="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500 bg-white"
        >
          <option value="">All Positions</option>
          {availablePositions.map(pos => (
            <option key={pos} value={pos}>{pos}</option>
          ))}
        </select>
      </div>
    </div>
  );
};

export default PlayerFilterControls;