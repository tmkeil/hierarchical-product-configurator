import React from 'react';
import type { SuccessorInfo } from '../api/client';

interface SuccessorWarningProps {
  successor: SuccessorInfo;
  onSwitchToNew?: () => void;
  onContinueWithOld?: () => void;
}

export const SuccessorWarning: React.FC<SuccessorWarningProps> = ({
  successor,
  onSwitchToNew,
  onContinueWithOld,
}) => {
  if (!successor.has_successor) {
    return null;
  }

  // Determine colors based on severity
  const severity = successor.warning_severity || 'info';
  const severityColors = {
    info: {
      bg: 'bg-blue-50',
      border: 'border-blue-400',
      text: 'text-blue-900',
      textLight: 'text-blue-700',
      icon: 'text-blue-600',
    },
    warning: {
      bg: 'bg-amber-50',
      border: 'border-amber-400',
      text: 'text-amber-900',
      textLight: 'text-amber-700',
      icon: 'text-amber-600',
    },
    critical: {
      bg: 'bg-red-50',
      border: 'border-red-500',
      text: 'text-red-900',
      textLight: 'text-red-700',
      icon: 'text-red-600',
    },
  };

  const colors = severityColors[severity];

  // Determine title based on replacement type
  const titles = {
    successor: 'Nachfolgeprodukt verfügbar',
    alternative: 'Alternative verfügbar',
    deprecated: 'Dieses Produkt wurde abgelöst',
  };

  const title = titles[successor.replacement_type || 'successor'];

  return (
    <div className={`mt-4 p-4 ${colors.bg} border-l-4 ${colors.border} rounded`}>
      <div className="flex items-start gap-3">
        {/* Icon */}
        <div className={`${colors.icon} mt-0.5`}>
          {severity === 'critical' && (
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          )}
          {severity === 'warning' && (
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          )}
          {severity === 'info' && (
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          )}
        </div>

        {/* Content */}
        <div className="flex-1">
          <h3 className={`font-semibold ${colors.text} text-lg mb-1`}>
            {title}
          </h3>

          {/* Target Product Info */}
          {successor.target_full_code && (
            <div className={`${colors.text} mb-2`}>
              <span className="font-medium">Neues Produkt:</span>{' '}
              <span className="font-mono bg-white/50 px-2 py-0.5 rounded">
                {successor.target_full_code}
              </span>
              {successor.target_label && (
                <span className={`block text-sm ${colors.textLight} mt-1`}>
                  {successor.target_label}
                </span>
              )}
            </div>
          )}

          {/* Migration Note */}
          {successor.migration_note && (
            <p className={`text-sm ${colors.textLight} mb-3`}>
              {successor.migration_note}
            </p>
          )}

          {/* Actions */}
          <div className="flex gap-2 mt-3">
            {onSwitchToNew && successor.target_full_code && (
              <button
                onClick={onSwitchToNew}
                className={`
                  px-4 py-2 rounded font-medium text-sm
                  ${severity === 'critical' 
                    ? 'bg-red-600 hover:bg-red-700 text-white' 
                    : severity === 'warning'
                    ? 'bg-amber-600 hover:bg-amber-700 text-white'
                    : 'bg-blue-600 hover:bg-blue-700 text-white'
                  }
                  transition-colors
                `}
              >
                Zum Nachfolger wechseln →
              </button>
            )}
            {onContinueWithOld && successor.allow_old_selection && (
              <button
                onClick={onContinueWithOld}
                className={`
                  px-4 py-2 rounded font-medium text-sm
                  border ${colors.border} ${colors.text}
                  hover:bg-white/50
                  transition-colors
                `}
              >
                Trotzdem fortfahren
              </button>
            )}
          </div>

          {/* Warning if old selection not allowed */}
          {!successor.allow_old_selection && (
            <div className="mt-3 text-sm font-medium text-red-700">
              ⚠️ Dieses Produkt kann nicht mehr bestellt werden
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

/**
 * Compact badge version for node-level warnings (Phase 2)
 */
interface SuccessorBadgeProps {
  successor: SuccessorInfo;
  onClick?: () => void;
}

export const SuccessorBadge: React.FC<SuccessorBadgeProps> = ({
  successor,
  onClick,
}) => {
  if (!successor.has_successor) {
    return null;
  }

  const severity = successor.warning_severity || 'info';
  
  const badgeColors = {
    info: 'bg-blue-100 text-blue-800 border-blue-300',
    warning: 'bg-amber-100 text-amber-800 border-amber-300',
    critical: 'bg-red-100 text-red-800 border-red-300',
  };

  const icons = {
    successor: '🔄',
    alternative: '💡',
    deprecated: '⚠️',
  };

  return (
    <div
      onClick={onClick}
      className={`
        inline-flex items-center gap-1.5 px-2 py-1 rounded text-xs font-medium border
        ${badgeColors[severity]}
        ${onClick ? 'cursor-pointer hover:shadow-sm transition-shadow' : ''}
      `}
      title={successor.migration_note || 'Nachfolger verfügbar'}
    >
      <span>{icons[successor.replacement_type || 'successor']}</span>
      <span>Nachfolger</span>
    </div>
  );
};
