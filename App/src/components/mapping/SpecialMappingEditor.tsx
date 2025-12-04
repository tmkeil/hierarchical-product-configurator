import React, { useState } from 'react';
import { Group, Picture, Link } from '../../types/mapping';

interface SpecialMappingEditorProps {
  group: Group;
  onUpdate: (group: Group) => void;
}

export const SpecialMappingEditor: React.FC<SpecialMappingEditorProps> = ({
  group,
  onUpdate,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [newLabelDe, setNewLabelDe] = useState('');
  const [newLabelEn, setNewLabelEn] = useState('');
  const [newPictureUrl, setNewPictureUrl] = useState('');
  const [newPictureDesc, setNewPictureDesc] = useState('');
  const [newLinkUrl, setNewLinkUrl] = useState('');
  const [newLinkDesc, setNewLinkDesc] = useState('');
  
  const hasSpecialMapping = group.specialMapping && 
    (group.specialMapping.positionRange || group.specialMapping.allowed);

  const updateSpecialMapping = (field: string, value: any) => {
    onUpdate({
      ...group,
      specialMapping: {
        ...group.specialMapping,
        [field]: value,
      },
    });
  };

  const clearSpecialMapping = () => {
    onUpdate({
      ...group,
      specialMapping: undefined,
    });
  };

  const addLabelDe = () => {
    if (!newLabelDe.trim()) return;
    const labels = group.specialMapping?.labelsDe || [];
    updateSpecialMapping('labelsDe', [...labels, newLabelDe]);
    setNewLabelDe('');
  };

  const addLabelEn = () => {
    if (!newLabelEn.trim()) return;
    const labels = group.specialMapping?.labelsEn || [];
    updateSpecialMapping('labelsEn', [...labels, newLabelEn]);
    setNewLabelEn('');
  };

  const removeLabelDe = (index: number) => {
    const labels = group.specialMapping?.labelsDe || [];
    updateSpecialMapping('labelsDe', labels.filter((_, i) => i !== index));
  };

  const removeLabelEn = (index: number) => {
    const labels = group.specialMapping?.labelsEn || [];
    updateSpecialMapping('labelsEn', labels.filter((_, i) => i !== index));
  };

  const addPicture = () => {
    if (!newPictureUrl.trim()) return;
    const pictures = group.specialMapping?.pictures || [];
    updateSpecialMapping('pictures', [...pictures, { url: newPictureUrl, description: newPictureDesc }]);
    setNewPictureUrl('');
    setNewPictureDesc('');
  };

  const removePicture = (index: number) => {
    const pictures = group.specialMapping?.pictures || [];
    updateSpecialMapping('pictures', pictures.filter((_, i) => i !== index));
  };

  const addLink = () => {
    if (!newLinkUrl.trim()) return;
    const links = group.specialMapping?.links || [];
    updateSpecialMapping('links', [...links, { url: newLinkUrl, description: newLinkDesc }]);
    setNewLinkUrl('');
    setNewLinkDesc('');
  };

  const removeLink = (index: number) => {
    const links = group.specialMapping?.links || [];
    updateSpecialMapping('links', links.filter((_, i) => i !== index));
  };

  return (
    <div className="border-t border-gray-200 pt-3">
      {/* Toggle Button */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between text-sm font-medium text-gray-700 hover:text-gray-900 mb-2"
      >
        <span className="flex items-center gap-2">
          ⚙️ Special Mapping
          {hasSpecialMapping && (
            <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">
              Aktiv
            </span>
          )}
        </span>
        <span className="text-gray-400">{isExpanded ? '▼' : '▶'}</span>
      </button>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="space-y-3 bg-gray-50 border border-gray-200 rounded p-3">
          {/* Info Box */}
          <div className="text-xs text-gray-600 bg-blue-50 border border-blue-200 rounded p-2">
            <p className="font-semibold mb-1">ℹ️ Special Mapping</p>
            <p>
              Definiert Positionsbereiche und erlaubte Zeichen für diese Gruppe. 
              Beispiel: Position "3-6" mit erlaubten Zeichen "1-4" oder "A-Z".
            </p>
          </div>

          {/* Position Range */}
          <div>
            <label className="text-xs text-gray-600 mb-1 block">
              Positionsbereich (optional)
            </label>
            <input
              type="text"
              value={group.specialMapping?.positionRange || ''}
              onChange={e => updateSpecialMapping('positionRange', e.target.value || undefined)}
              placeholder="z.B. 3-6, 5-8, ..."
              className="w-full px-3 py-1.5 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
            />
          </div>

          {/* Allowed Characters */}
          <div>
            <label className="text-xs text-gray-600 mb-1 block">
              Erlaubte Zeichen (optional)
            </label>
            <input
              type="text"
              value={group.specialMapping?.allowed || ''}
              onChange={e => updateSpecialMapping('allowed', e.target.value || undefined)}
              placeholder="z.B. 1-4, 0-Z, A-Z, B-I, ..."
              className="w-full px-3 py-1.5 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
            />
            <div className="text-xs text-gray-500 mt-1">
              Beispiele: <code>1-4</code> (Ziffern), <code>0-Z</code> (Alphanumerisch), 
              <code>A-Z</code> (Buchstaben), <code>B-I</code> (Bereich)
            </div>
          </div>

          <div className="border-t border-gray-200 pt-3 mt-3">
            <h4 className="text-sm font-semibold text-gray-700 mb-2">Labels & Medien</h4>

            {/* Labels DE */}
            <div className="mb-3">
              <label className="text-xs text-gray-600 mb-1 block">Labels (DE)</label>
              <div className="flex gap-2 mb-2">
                <input
                  type="text"
                  value={newLabelDe}
                  onChange={e => setNewLabelDe(e.target.value)}
                  onKeyPress={e => e.key === 'Enter' && addLabelDe()}
                  placeholder="Label hinzufügen"
                  className="flex-1 px-3 py-1.5 border border-gray-300 rounded text-sm"
                />
                <button
                  onClick={addLabelDe}
                  className="px-3 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
                >
                  +
                </button>
              </div>
              {(group.specialMapping?.labelsDe || []).map((label, idx) => (
                <div key={idx} className="flex items-center gap-2 mb-1 text-sm">
                  <span className="flex-1 px-2 py-1 bg-gray-100 rounded">{label}</span>
                  <button
                    onClick={() => removeLabelDe(idx)}
                    className="text-red-600 hover:text-red-700 text-xs"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>

            {/* Labels EN */}
            <div className="mb-3">
              <label className="text-xs text-gray-600 mb-1 block">Labels (EN)</label>
              <div className="flex gap-2 mb-2">
                <input
                  type="text"
                  value={newLabelEn}
                  onChange={e => setNewLabelEn(e.target.value)}
                  onKeyPress={e => e.key === 'Enter' && addLabelEn()}
                  placeholder="Label hinzufügen"
                  className="flex-1 px-3 py-1.5 border border-gray-300 rounded text-sm"
                />
                <button
                  onClick={addLabelEn}
                  className="px-3 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
                >
                  +
                </button>
              </div>
              {(group.specialMapping?.labelsEn || []).map((label, idx) => (
                <div key={idx} className="flex items-center gap-2 mb-1 text-sm">
                  <span className="flex-1 px-2 py-1 bg-gray-100 rounded">{label}</span>
                  <button
                    onClick={() => removeLabelEn(idx)}
                    className="text-red-600 hover:text-red-700 text-xs"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>

            {/* Pictures */}
            <div className="mb-3">
              <label className="text-xs text-gray-600 mb-1 block">Bilder</label>
              <div className="space-y-2 mb-2">
                <input
                  type="text"
                  value={newPictureUrl}
                  onChange={e => setNewPictureUrl(e.target.value)}
                  placeholder="URL (relativ zu /uploads)"
                  className="w-full px-3 py-1.5 border border-gray-300 rounded text-sm"
                />
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={newPictureDesc}
                    onChange={e => setNewPictureDesc(e.target.value)}
                    onKeyPress={e => e.key === 'Enter' && addPicture()}
                    placeholder="Beschreibung (optional)"
                    className="flex-1 px-3 py-1.5 border border-gray-300 rounded text-sm"
                  />
                  <button
                    onClick={addPicture}
                    className="px-3 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
                  >
                    + Bild
                  </button>
                </div>
              </div>
              {(group.specialMapping?.pictures || []).map((pic, idx) => (
                <div key={idx} className="flex items-start gap-2 mb-2 p-2 bg-gray-100 rounded text-xs">
                  <div className="flex-1">
                    <div className="font-semibold">{pic.url}</div>
                    {pic.description && <div className="text-gray-600">{pic.description}</div>}
                  </div>
                  <button
                    onClick={() => removePicture(idx)}
                    className="text-red-600 hover:text-red-700"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>

            {/* Links */}
            <div className="mb-3">
              <label className="text-xs text-gray-600 mb-1 block">Links</label>
              <div className="space-y-2 mb-2">
                <input
                  type="text"
                  value={newLinkUrl}
                  onChange={e => setNewLinkUrl(e.target.value)}
                  placeholder="URL (https://...)"
                  className="w-full px-3 py-1.5 border border-gray-300 rounded text-sm"
                />
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={newLinkDesc}
                    onChange={e => setNewLinkDesc(e.target.value)}
                    onKeyPress={e => e.key === 'Enter' && addLink()}
                    placeholder="Beschreibung (optional)"
                    className="flex-1 px-3 py-1.5 border border-gray-300 rounded text-sm"
                  />
                  <button
                    onClick={addLink}
                    className="px-3 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
                  >
                    + Link
                  </button>
                </div>
              </div>
              {(group.specialMapping?.links || []).map((link, idx) => (
                <div key={idx} className="flex items-start gap-2 mb-2 p-2 bg-gray-100 rounded text-xs">
                  <div className="flex-1">
                    <div className="font-semibold">{link.url}</div>
                    {link.description && <div className="text-gray-600">{link.description}</div>}
                  </div>
                  <button
                    onClick={() => removeLink(idx)}
                    className="text-red-600 hover:text-red-700"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Clear Button */}
          {hasSpecialMapping && (
            <button
              onClick={clearSpecialMapping}
              className="text-xs text-red-600 hover:text-red-700 underline"
            >
              Special Mapping entfernen
            </button>
          )}
        </div>
      )}
    </div>
  );
};