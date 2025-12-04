/**
 * Admin Panel Component
 * 
 * Features:
 * - User Management (nur für Admins)
 * - User Liste anzeigen
 * - Neue Users erstellen (via Modal)
 * - Navigation zurück zur Main Page
 */

import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

interface User {
  id: number;
  username: string;
  role: 'admin' | 'user';
  is_active: boolean;
  must_change_password: boolean;
  created_at: string;
}

interface CreateUserRequest {
  username: string;
  password: string;
  role: 'admin' | 'user';
}

export function AdminPanel() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal State
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [formData, setFormData] = useState<CreateUserRequest>({
    username: '',
    password: '',
    role: 'user'
  });
  const [formError, setFormError] = useState<string | null>(null);
  const [formLoading, setFormLoading] = useState(false);
  const [usernameExists, setUsernameExists] = useState(false);

  // Load Users
  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('auth_token');
      const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE_URL}/api/admin/users`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to load users');
      }

      const data = await response.json();
      setUsers(data);

    } catch (err: any) {
      console.error('Load users error:', err);
      setError(err.message || 'Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteUser = async (userId: number, username: string) => {
    if (!confirm(`Are you sure you want to delete user "${username}"?`)) {
      return;
    }

    try {
      setError(null);

      const token = localStorage.getItem('auth_token');
      const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE_URL}/api/admin/users/${userId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to delete user');
      }

      // Reload users after successful deletion
      await loadUsers();

    } catch (err: any) {
      console.error('Delete user error:', err);
      setError(err.message || 'Failed to delete user');
    }
  };

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
    if (!formData.username || !formData.password) {
      setFormError('All fields are required');
      return;
    }

    if (formData.password.length < 8) {
      setFormError('Password must be at least 8 characters');
      return;
    }

    try {
      setFormError(null);
      setFormLoading(true);

      const token = localStorage.getItem('auth_token');
      const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE_URL}/api/admin/users`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create user');
      }

      // Erfolg! Reload Users & Close Modal & Reset Form
      await loadUsers();
      setShowCreateModal(false);
      setFormData({
        username: '',
        password: '',
        role: 'user'
      });
      setFormError(null);

    } catch (err: any) {
      console.error('Create user error:', err);
      setFormError(err.message || 'Failed to create user');
    } finally {
      setFormLoading(false);
    }
  };

  const handleCloseModal = () => {
    setShowCreateModal(false);
    setFormData({
      username: '',
      password: '',
      role: 'user'
    });
    setFormError(null);
    setUsernameExists(false);
  };

  // Live-Check ob Username bereits existiert
  const checkUsernameExists = (username: string) => {
    if (!username) {
      setUsernameExists(false);
      return;
    }
    const exists = users.some(u => u.username.toLowerCase() === username.toLowerCase());
    setUsernameExists(exists);
  };



  // Nur Admins dürfen Admin Panel sehen
  if (user?.role !== 'admin') {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen gap-4">
        <h1 className="text-2xl font-bold text-red-600">403 - Forbidden</h1>
        <p className="text-gray-600">You don't have permission to access this page.</p>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-gray-50 flex flex-col">
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Header with Navigation */}
        <div className="mb-8 flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">User Management</h1>
            <p className="text-gray-600">Manage users and permissions</p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => navigate('/mapping-tool')}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium flex items-center gap-2"
            >
              🗺️ Mapping Tool
            </button>
            <button
              onClick={() => navigate('/')}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors font-medium flex items-center gap-2"
            >
              ← Back to Main
            </button>
          </div>
        </div>

        {/* Create User Button */}
        <div className="mb-6">
          <button
            onClick={() => {
              // Reset Form beim Öffnen
              setFormData({
                username: '',
                password: '',
                role: 'user'
              });
              setFormError(null);
              setUsernameExists(false);
              setShowCreateModal(true);
            }}
            className="px-6 py-2.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors font-medium shadow-sm"
          >
            + Create New User
          </button>
        </div>

        {/* Users Table */}
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">Users</h2>
          </div>

          {loading ? (
            <div className="p-8 text-center text-gray-600">Loading users...</div>
          ) : error ? (
            <div className="p-8 text-center text-red-600">{error}</div>
          ) : users.length === 0 ? (
            <div className="p-8 text-center text-gray-600">No users found</div>
          ) : (
            <div className="overflow-x-auto max-h-96 overflow-y-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200 sticky top-0">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Username</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Role</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Must Change Password</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Created</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {users.map((u) => (
                    <tr key={u.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-6 py-4 text-sm font-medium text-gray-900">{u.username}</td>
                      <td className="px-6 py-4 text-sm">
                        <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                          u.role === 'admin' 
                            ? 'bg-purple-100 text-purple-800' 
                            : 'bg-blue-100 text-blue-800'
                        }`}>
                          {u.role}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm">
                        <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                          u.is_active 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {u.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm">
                        <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                          u.must_change_password 
                            ? 'bg-yellow-100 text-yellow-800' 
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {u.must_change_password ? 'Yes' : 'No'}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-700">
                        {new Date(u.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 text-sm">
                        <button
                          onClick={() => handleDeleteUser(u.id, u.username)}
                          disabled={u.id === 1}
                          className={`px-3 py-1 rounded text-xs font-semibold transition-colors ${
                            u.id === 1
                              ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                              : 'bg-red-600 text-white hover:bg-red-700'
                          }`}
                          title={u.id === 1 ? 'Cannot delete initial admin' : 'Delete user'}
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
        </div>

        {/* Create User Modal */}
        {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md">
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
              <h2 className="text-xl font-semibold text-gray-900">Create New User</h2>
              <button
                onClick={handleCloseModal}
                disabled={formLoading}
                className="text-gray-400 hover:text-gray-600 text-2xl leading-none disabled:cursor-not-allowed"
              >
                ×
              </button>
            </div>

            {/* Modal Content */}
            <form onSubmit={handleCreateUser} className="p-6 space-y-4">
              {/* Username */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Username
                </label>
                <input
                  type="text"
                  value={formData.username}
                  onChange={(e) => {
                    setFormData({ ...formData, username: e.target.value });
                    checkUsernameExists(e.target.value);
                  }}
                  placeholder="Enter username"
                  disabled={formLoading}
                  className={`w-full px-4 py-2.5 text-sm border rounded-lg focus:ring-2 outline-none transition-all disabled:bg-gray-100 ${
                    usernameExists 
                      ? 'border-red-500 focus:ring-red-500 focus:border-red-500' 
                      : 'border-gray-300 focus:ring-indigo-500 focus:border-transparent'
                  }`}
                />
                {usernameExists && (
                  <p className="text-xs text-red-600 mt-1">This username already exists</p>
                )}
              </div>

              {/* Password */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Initial Password
                </label>
                <input
                  type="text"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  placeholder="Enter initial password (min 8 characters)"
                  disabled={formLoading}
                  className="w-full px-4 py-2.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all disabled:bg-gray-100"
                />
                <p className="text-xs text-gray-500 mt-1">User will be prompted to change password on first login</p>
              </div>

              {/* Role */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Role
                </label>
                <select
                  value={formData.role}
                  onChange={(e) => setFormData({ ...formData, role: e.target.value as 'admin' | 'user' })}
                  disabled={formLoading}
                  className="w-full px-4 py-2.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all disabled:bg-gray-100"
                >
                  <option value="user">User</option>
                  <option value="admin">Admin</option>
                </select>
              </div>

              {/* Error Message */}
              {formError && (
                <div className="p-3 bg-red-100 border border-red-300 rounded-lg text-red-700 text-sm">
                  {formError}
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-3 pt-2">
                <button
                  type="submit"
                  disabled={formLoading || usernameExists}
                  className="flex-1 py-2.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors font-medium disabled:bg-gray-400 disabled:cursor-not-allowed"
                >
                  {formLoading ? 'Creating...' : 'Create User'}
                </button>
                <button
                  type="button"
                  onClick={handleCloseModal}
                  disabled={formLoading}
                  className="px-6 py-2.5 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors font-medium disabled:cursor-not-allowed"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      </div>
    </div>
  );
}
