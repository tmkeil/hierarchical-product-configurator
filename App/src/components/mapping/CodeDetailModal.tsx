import React, { useState } from 'react';
import { createPortal } from 'react-dom';
import { Code } from '../../types/mapping';

interface CodeDetailModalProps {
  code: Code;
  onSave: (updatedCode: Code) => void;
  onClose: () => void;
}

export const CodeDetailModal: React.FC<CodeDetailModalProps> = ({ code, onSave, onClose }) => {
  const [editedCode, setEditedCode] = useState<Code>(code);

  const addPicture = () => {
    setEditedCode(prev => ({
      ...prev,
      pictures: [...prev.pictures, { url: '', description: '' }],
    }));
  };

  const updatePicture = (index: number, field: 'url' | 'description', value: string) => {
    setEditedCode(prev => ({
      ...prev,
      pictures: prev.pictures.map((pic, i) =>
        i === index ? { ...pic, [field]: value } : pic
      ),
    }));
  };

  const deletePicture = (index: number) => {
    setEditedCode(prev => ({
      ...prev,
      pictures: prev.pictures.filter((_, i) => i !== index),
    }));
  };

  const addLink = () => {
    setEditedCode(prev => ({
      ...prev,
      links: [...prev.links, { url: '', description: '' }],
    }));
  };

  const updateLink = (index: number, field: 'url' | 'description', value: string) => {
    setEditedCode(prev => ({
      ...prev,
      links: prev.links.map((link, i) =>
        i === index ? { ...link, [field]: value } : link
      ),
    }));
  };

  const deleteLink = (index: number) => {
    setEditedCode(prev => ({
      ...prev,
      links: prev.links.filter((_, i) => i !== index),
    }));
  };

  const handleSave = () => {
    onSave(editedCode);
    onClose();
  };

  return createPortal(
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div 
        className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b border-gray-200">
          <div>
            <h2 className="text-xl font-bold text-gray-900">
              Code Details: <span className="font-mono text-blue-600">{code.value}</span>
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              Beschreibungen, Bilder und Links bearbeiten
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="overflow-y-auto flex-1 p-6 space-y-6">
          {/* Beschreibungen */}
          <div>
            <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              📝 Beschreibungen
            </h3>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-3">
              <p className="text-xs text-blue-800">
                <strong>Hinweis:</strong> Geben Sie hier nur die reine Beschreibung ein. 
                Der label_mapper.py generiert automatisch das komplette Format mit Titel, Code, etc.
              </p>
            </div>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Deutsch (DE)
                </label>
                <input
                  type="text"
                  value={editedCode.labelDe}
                  onChange={e => setEditedCode(prev => ({ ...prev, labelDe: e.target.value }))}
                  placeholder="Beschreibung auf Deutsch"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Englisch (EN)
                </label>
                <input
                  type="text"
                  value={editedCode.labelEn || ''}
                  onChange={e => setEditedCode(prev => ({ ...prev, labelEn: e.target.value }))}
                  placeholder="Description in English"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
          </div>

          {/* Bilder */}
          <div>
            <div className="flex justify-between items-center mb-3">
              <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                🖼️ Bilder ({editedCode.pictures.length})
              </h3>
              <button
                onClick={addPicture}
                className="text-sm px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                + Bild
              </button>
            </div>
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mb-3">
              <p className="text-xs text-amber-800">
                <strong>Bild-URL:</strong> Relativer Pfad zum <code className="bg-amber-100 px-1 rounded">/uploads</code> Ordner<br/>
                Beispiel: <code className="bg-amber-100 px-1 rounded">products/bes/housing_metal.jpg</code>
              </p>
            </div>
            <div className="space-y-3">
              {editedCode.pictures.map((picture, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-3 bg-gray-50">
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-xs font-medium text-gray-500">Bild {index + 1}</span>
                    <button
                      onClick={() => deletePicture(index)}
                      className="text-red-600 hover:text-red-700 text-sm"
                    >
                      ✕
                    </button>
                  </div>
                  <div className="space-y-2">
                    <input
                      type="text"
                      value={picture.url}
                      onChange={e => updatePicture(index, 'url', e.target.value)}
                      placeholder="z.B. products/bes/housing_metal.jpg"
                      className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono"
                    />
                    <input
                      type="text"
                      value={picture.description}
                      onChange={e => updatePicture(index, 'description', e.target.value)}
                      placeholder="Bildbeschreibung"
                      className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                </div>
              ))}
              {editedCode.pictures.length === 0 && (
                <p className="text-sm text-gray-400 italic text-center py-4">
                  Keine Bilder vorhanden
                </p>
              )}
            </div>
          </div>

          {/* Links */}
          <div>
            <div className="flex justify-between items-center mb-3">
              <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                🔗 Links ({editedCode.links.length})
              </h3>
              <button
                onClick={addLink}
                className="text-sm px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                + Link
              </button>
            </div>
            <div className="space-y-3">
              {editedCode.links.map((link, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-3 bg-gray-50">
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-xs font-medium text-gray-500">Link {index + 1}</span>
                    <button
                      onClick={() => deleteLink(index)}
                      className="text-red-600 hover:text-red-700 text-sm"
                    >
                      ✕
                    </button>
                  </div>
                  <div className="space-y-2">
                    <input
                      type="text"
                      value={link.url}
                      onChange={e => updateLink(index, 'url', e.target.value)}
                      placeholder="Link-URL (https://...)"
                      className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                    <input
                      type="text"
                      value={link.description}
                      onChange={e => updateLink(index, 'description', e.target.value)}
                      placeholder="Link-Beschreibung"
                      className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                </div>
              ))}
              {editedCode.links.length === 0 && (
                <p className="text-sm text-gray-400 italic text-center py-4">
                  Keine Links vorhanden
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 p-6 bg-gray-50 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Abbrechen
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Speichern
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
};
