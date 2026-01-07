import { useQuery } from '@tanstack/react-query';
import { fetchNodeSuccessor, type AvailableOption } from '../api/client';
import { SuccessorBadge } from './SuccessorWarning';

interface OptionCardProps {
  option: AvailableOption;
  level: number;
  index: number;
  isSelected: boolean;
  isCompatible: boolean;
  onSelect: (option: AvailableOption) => void;
  onEdit: (option: AvailableOption) => void;
  onMouseEnter: (option: AvailableOption) => void;
  onMouseLeave: () => void;
  formatDisplay: (option: AvailableOption) => React.ReactNode;
}

export const OptionCard: React.FC<OptionCardProps> = ({
  option,
  level,
  index,
  isSelected,
  isCompatible,
  onSelect,
  onEdit,
  onMouseEnter,
  onMouseLeave,
  formatDisplay,
}) => {
  // Query successor info for this node
  const successorQuery = useQuery({
    queryKey: ['node-successor', option.id],
    queryFn: () => fetchNodeSuccessor(option.id!),
    enabled: !!option.id,
    staleTime: 60000, // 1 minute cache
  });

  const hasSuccessor = successorQuery.data?.has_successor || false;

  return (
    <div
      key={`${level}-${option.code}-${option.position}-${index}`}
      className={`flex items-center justify-between px-4 py-2.5 hover:bg-${isCompatible ? 'blue' : 'gray'}-50 text-${isCompatible ? 'gray-900' : 'gray-400'} ${
        isSelected ? `bg-${isCompatible ? 'blue' : 'gray'}-100` : ''
      } relative`}
      onMouseEnter={() => onMouseEnter(option)}
      onMouseLeave={onMouseLeave}
    >
      <span 
        className="flex-1 cursor-pointer"
        onClick={() => onSelect(option)}
      >
        {formatDisplay(option)}
      </span>

      {/* Successor Badge - zeigt wenn Node deprecated ist */}
      {hasSuccessor && successorQuery.data && (
        <div className="mr-2">
          <SuccessorBadge successor={successorQuery.data} />
        </div>
      )}

      {/* Edit Button */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          onEdit(option);
        }}
        className={`ml-2 p-1 text-${isCompatible ? 'blue' : 'gray'}-600 hover:text-${isCompatible ? 'blue' : 'gray'}-800 hover:bg-${isCompatible ? 'blue' : 'gray'}-100 rounded transition-colors`}
        title="Edit node details"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </button>
    </div>
  );
};
