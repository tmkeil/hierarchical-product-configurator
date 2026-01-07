/**
 * Product Lifecycle Management (Admin Only)
 * 
 * Vereinfachte Version - nur Liste + Löschen
 * Hinzufügen erfolgt über Main-Seite mit Tree-Selector
 */

import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  fetchAllSuccessors,
  deleteSuccessor,
} from '../api/client';

export const ProductLifecycle: React.FC = () => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  // Fetch all successors
  const { data, isLoading, error } = useQuery({
    queryKey: ['admin-successors'],
    queryFn: fetchAllSuccessors,
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: deleteSuccessor,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-successors'] });
      queryClient.invalidateQueries({ queryKey: ['product-successor'] });
      queryClient.invalidateQueries({ queryKey: ['children'] });
      queryClient.invalidateQueries({ queryKey: ['options'] });
    },
    onError: (error: any) => {
      console.error('Fehler beim Löschen der Nachfolger-Verlinkung:', error);
    },
  });

  const handleDelete = (id: number, sourceLabel: string, groupIds?: number[]) => {
    const itemCount = groupIds ? groupIds.length : 1;
    const confirmMsg = groupIds 
      ? `Alle ${itemCount} Verlinkungen für "${sourceLabel}" wirklich löschen?`
      : `Nachfolger-Verlinkung für "${sourceLabel}" wirklich löschen?`;
    
    if (confirm(confirmMsg)) {
      if (groupIds) {
        // Delete all in group sequentially
        Promise.all(groupIds.map(gid => deleteMutation.mutateAsync(gid)))
          .then(() => {
            queryClient.invalidateQueries({ queryKey: ['admin-successors'] });
            queryClient.invalidateQueries({ queryKey: ['product-successor'] });
            queryClient.invalidateQueries({ queryKey: ['children'] });
            queryClient.invalidateQueries({ queryKey: ['options'] });
          })
          .catch((error: any) => {
            console.error('Fehler beim Löschen:', error);
          });
      } else {
        deleteMutation.mutate(id);
      }
    }
  };

  // Group successors by source_code + target_code combination
  const groupedSuccessors = React.useMemo(() => {
    if (!data?.successors) return [];

    const groups = new Map<string, {
      ids: number[];
      source_display: string;
      target_display: string;
      source_family?: string;
      target_family?: string;
      source_level?: number;
      target_level?: number;
      source_type: string;
      is_mixed: boolean;  // Produkt → Node oder Node → Produkt
      is_complete: boolean;  // Beide sind komplette Produkte
      migration_note?: string | null;
      created_at: string;
      created_by?: string | null;
    }>();

    for (const successor of data.successors) {
      // DEBUG: Log target family code
      console.log('Successor:', {
        source_code: successor.source_code,
        source_family: successor.source_family_code,
        target_code: successor.target_code,
        target_family: successor.target_family_code,
        target_typecode: successor.target_typecode,
        target_level: successor.target_level
      });
      
      // Use level directly from database
      const sourceLevel = successor.source_level;
      const targetLevel = successor.target_level;

      // Extract code and family from typecode
      let sourceCode: string;
      let sourceFamily: string | undefined;
      let targetCode: string;
      let targetFamily: string | undefined;

      // Parse source - use full path for products (level > 1), just code for nodes (level 1)
      // Family always comes from DB via closure table
      sourceFamily = successor.source_family_code || undefined;
      
      if (successor.source_typecode) {
        const parts = successor.source_typecode.split(' ');
        
        if (sourceLevel && sourceLevel > 1) {
          sourceCode = parts[1] || successor.source_typecode; // "Z003-020" (full path)
        } else {
          const pathParts = parts[1]?.split('-') || [];
          sourceCode = pathParts[pathParts.length - 1] || successor.source_typecode; // "020" (just code)
        }
      } else {
        sourceCode = successor.source_code; // USE CODE, NOT LABEL!
      }

      // Parse target - use full path for products (level > 1), just code for nodes (level 1)
      // Family always comes from DB via closure table
      targetFamily = successor.target_family_code || undefined;
      
      if (successor.target_typecode) {
        const parts = successor.target_typecode.split(' ');
        
        if (targetLevel && targetLevel > 1) {
          targetCode = parts[1] || successor.target_typecode; // "Z003-007" (full path)
        } else {
          const pathParts = parts[1]?.split('-') || [];
          targetCode = pathParts[pathParts.length - 1] || successor.target_typecode; // "007" (just code)
        }
      } else if (successor.target_full_code) {
        const parts = successor.target_full_code.split(' ');
        
        if (targetLevel && targetLevel > 1) {
          targetCode = parts[1] || successor.target_full_code;
        } else {
          const pathParts = parts[1]?.split('-') || [];
          targetCode = pathParts[pathParts.length - 1] || successor.target_full_code;
        }
      } else {
        targetCode = successor.target_code || 'Unknown'; // USE CODE, NOT LABEL!
      }

      // Determine type: complete product, node, or mixed
      const sourceIsComplete = successor.source_type === 'leaf' || successor.source_type === 'intermediate';
      const targetIsComplete = successor.target_typecode !== null; // Has full typecode
      const isComplete = sourceIsComplete && targetIsComplete;
      const isMixed = sourceIsComplete !== targetIsComplete;
      
      const groupKey = `${sourceCode}@${sourceLevel || '?'}→${targetCode}@${targetLevel || '?'}`;

      if (!groups.has(groupKey)) {
        groups.set(groupKey, {
          ids: [successor.id],
          source_display: sourceCode,
          target_display: targetCode,
          source_family: sourceFamily,
          target_family: targetFamily,
          source_level: sourceLevel,
          target_level: targetLevel,
          source_type: successor.source_type,
          is_mixed: isMixed,
          is_complete: isComplete,
          migration_note: successor.migration_note,
          created_at: successor.created_at,
          created_by: successor.created_by,
        });
      } else {
        groups.get(groupKey)!.ids.push(successor.id);
      }
    }

    return Array.from(groups.values());
  }, [data]);

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">🔗 Product Lifecycle Management</h1>
            <p className="text-gray-600 mt-2">
              Verwaltung von Nachfolger-Verlinkungen
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => navigate('/admin')}
              className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg font-medium"
            >
              ← Zurück zum Admin Panel
            </button>
            <button
              onClick={() => navigate('/')}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium"
            >
              + Neue Verlinkung erstellen
            </button>
          </div>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <div className="flex items-start gap-3">
            <div className="text-2xl">ℹ️</div>
            <div>
              <div className="font-semibold text-blue-900">Wie erstelle ich eine neue Verlinkung?</div>
              <ol className="text-sm text-blue-700 mt-2 space-y-1 list-decimal list-inside">
                <li>Gehe zur <strong>Hauptseite</strong> (Button oben rechts)</li>
                <li>Wähle das <strong>alte Produkt/Node</strong> aus dem Produktbaum</li>
                <li>Klicke auf <strong>"+ Nachfolger hinzufügen"</strong> (orangener Button)</li>
                <li>Wähle den <strong>Nachfolger</strong> aus dem gleichen Produktbaum</li>
                <li>Klicke auf <strong>"✓ Verlinkung erstellen"</strong></li>
              </ol>
              <div className="text-xs text-blue-600 mt-2">
                💡 Tipp: Es werden automatisch ALLE gefilterten Nodes mit gleichem Code verlinkt (wie im Konfigurator)
              </div>
            </div>
          </div>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="text-center py-12">
            <div className="text-gray-500">Lade Verlinkungen...</div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
            ❌ Fehler beim Laden: {(error as Error).message}
          </div>
        )}

        {/* Successor List */}
        {data && (
          <div className="bg-white rounded-lg shadow">
            {groupedSuccessors.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                <div className="text-4xl mb-3">📭</div>
                <div className="text-lg font-medium">Keine Verlinkungen vorhanden</div>
                <div className="text-sm mt-2">
                  Gehe zur Hauptseite und erstelle die erste Verlinkung!
                </div>
              </div>
            ) : (
              <>
                <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
                  <div className="text-sm font-semibold text-gray-700">
                    {groupedSuccessors.length} Verlinkung{groupedSuccessors.length !== 1 ? 'en' : ''} 
                    <span className="text-gray-500 font-normal ml-2">
                      ({data.successors.length} Einzeleinträge)
                    </span>
                  </div>
                </div>
                
                <div className="divide-y divide-gray-200">
                  {groupedSuccessors.map((group, index) => (
                    <div
                      key={index}
                      className="px-6 py-3 hover:bg-gray-50 transition-colors group"
                    >
                      <div className="flex items-center justify-between gap-4">
                        {/* Type Badge */}
                        <div className="flex-shrink-0">
                          {group.is_complete ? (
                            <div className="w-2 h-2 rounded-full bg-green-500" title="Produkt-Link" />
                          ) : group.is_mixed ? (
                            <div className="w-2 h-2 rounded-full bg-orange-500" title="Gemischt" />
                          ) : (
                            <div className="w-2 h-2 rounded-full bg-blue-500" title="Node-Referenz" />
                          )}
                        </div>

                        {/* Source → Target (horizontal, compact, fixed widths) */}
                        <div className="flex items-center gap-4 flex-1 min-w-0">
                          {/* Source */}
                          <div className="flex items-center gap-2 w-72">
                            <span className="px-1.5 py-0.5 bg-gray-100 text-gray-600 text-xs font-semibold rounded flex-shrink-0">L{group.source_level}</span>
                            <span className="font-mono font-semibold text-gray-900">{group.source_display}</span>
                            <span className="text-xs text-gray-400 flex-shrink-0">{group.source_family || ''}</span>
                          </div>

                          <span className="text-gray-400 text-lg flex-shrink-0">→</span>

                          {/* Target */}
                          <div className="flex items-center gap-2 w-72">
                            <span className="px-1.5 py-0.5 bg-green-100 text-green-600 text-xs font-semibold rounded flex-shrink-0">L{group.target_level}</span>
                            <span className="font-mono font-semibold text-green-700">{group.target_display}</span>
                            <span className="text-xs text-gray-400 flex-shrink-0">{group.target_family || ''}</span>
                          </div>

                          {/* Multi-Node Badge */}
                          {group.ids.length > 1 && (
                            <span className="px-2 py-0.5 bg-purple-100 text-purple-700 text-xs font-semibold rounded-full flex-shrink-0">
                              ×{group.ids.length}
                            </span>
                          )}
                        </div>

                        {/* Metadata - compact, always visible */}
                        <div className="flex items-center gap-3 text-xs text-gray-400">
                          <span>{new Date(group.created_at).toLocaleDateString('de-DE')}</span>
                          
                          {/* Delete Button */}
                          <button
                            onClick={() => handleDelete(
                              group.ids[0], 
                              `${group.source_display} → ${group.target_display}`,
                              group.ids.length > 1 ? group.ids : undefined
                            )}
                            disabled={deleteMutation.isPending}
                            className="px-2 py-1 text-red-600 hover:bg-red-50 rounded disabled:opacity-50 opacity-0 group-hover:opacity-100 transition-opacity"
                          >
                            ✕
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
