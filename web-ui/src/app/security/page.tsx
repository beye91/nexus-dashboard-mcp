'use client';

import { useEffect, useState, useCallback } from 'react';
import Navigation from '@/components/Navigation';
import SearchableOperationsDropdown from '@/components/SearchableOperationsDropdown';
import { api } from '@/lib/api-client';
import type { SecurityConfig, User, Role, CreateUserRequest, CreateRoleRequest } from '@/types';

type TabType = 'users' | 'roles' | 'settings';

export default function SecurityPage() {
  const [activeTab, setActiveTab] = useState<TabType>('users');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Users state
  const [users, setUsers] = useState<User[]>([]);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [showUserModal, setShowUserModal] = useState(false);

  // Roles state
  const [roles, setRoles] = useState<Role[]>([]);
  const [editingRole, setEditingRole] = useState<Role | null>(null);
  const [showRoleModal, setShowRoleModal] = useState(false);

  // Settings state
  const [config, setConfig] = useState<SecurityConfig | null>(null);
  const [editMode, setEditMode] = useState(false);

  // API Token state
  const [showTokenModal, setShowTokenModal] = useState(false);
  const [generatedToken, setGeneratedToken] = useState<string | null>(null);
  const [tokenUsername, setTokenUsername] = useState<string>('');

  // Form states
  const [userForm, setUserForm] = useState<CreateUserRequest & { role_ids: number[] }>({
    username: '',
    password: '',
    email: '',
    display_name: '',
    is_superuser: false,
    role_ids: [],
  });

  const [roleForm, setRoleForm] = useState<CreateRoleRequest>({
    name: '',
    description: '',
    edit_mode_enabled: false,
    operations: [],
  });

  // Fetch data based on active tab
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        if (activeTab === 'users') {
          const [usersRes, rolesRes] = await Promise.all([
            api.users.list(),
            api.roles.list(),
          ]);
          setUsers(usersRes.data);
          setRoles(rolesRes.data);
        } else if (activeTab === 'roles') {
          const rolesRes = await api.roles.list();
          setRoles(rolesRes.data);
        } else if (activeTab === 'settings') {
          const [configRes, editModeRes] = await Promise.all([
            api.security.getConfig(),
            api.security.getEditMode(),
          ]);
          setConfig(configRes.data);
          setEditMode(editModeRes.data.enabled);
        }
        setError(null);
      } catch (err: any) {
        console.error('Failed to fetch data:', err);
        setError(err.response?.data?.detail || 'Failed to load data');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [activeTab]);

  // Show success message
  const showSuccess = useCallback((message: string) => {
    setSuccess(message);
    setTimeout(() => setSuccess(null), 3000);
  }, []);

  // User CRUD operations
  const handleCreateUser = async () => {
    try {
      await api.users.create(userForm);
      showSuccess('User created successfully');
      setShowUserModal(false);
      resetUserForm();
      // Refresh users list
      const res = await api.users.list();
      setUsers(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create user');
    }
  };

  const handleUpdateUser = async () => {
    if (!editingUser) return;
    try {
      await api.users.update(editingUser.id, {
        email: userForm.email || undefined,
        display_name: userForm.display_name || undefined,
        is_superuser: userForm.is_superuser,
        password: userForm.password || undefined,
      });
      if (userForm.role_ids.length > 0 || editingUser.roles.length > 0) {
        await api.users.assignRoles(editingUser.id, { role_ids: userForm.role_ids });
      }
      showSuccess('User updated successfully');
      setShowUserModal(false);
      setEditingUser(null);
      resetUserForm();
      const res = await api.users.list();
      setUsers(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update user');
    }
  };

  const handleDeleteUser = async (userId: number) => {
    if (!confirm('Are you sure you want to delete this user?')) return;
    try {
      await api.users.delete(userId);
      showSuccess('User deleted successfully');
      const res = await api.users.list();
      setUsers(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete user');
    }
  };

  const handleRegenerateToken = async (user: User) => {
    if (!confirm(`Regenerate API token for ${user.username}? The old token will stop working immediately.`)) return;
    try {
      const res = await api.users.regenerateToken(user.id);
      setGeneratedToken(res.data.api_token);
      setTokenUsername(user.username);
      setShowTokenModal(true);
      showSuccess('API token regenerated successfully');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to regenerate token');
    }
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      showSuccess('Copied to clipboard');
    } catch (err) {
      setError('Failed to copy to clipboard');
    }
  };

  const resetUserForm = () => {
    setUserForm({
      username: '',
      password: '',
      email: '',
      display_name: '',
      is_superuser: false,
      role_ids: [],
    });
  };

  const openUserModal = (user?: User) => {
    if (user) {
      setEditingUser(user);
      setUserForm({
        username: user.username,
        password: '',
        email: user.email || '',
        display_name: user.display_name || '',
        is_superuser: user.is_superuser,
        role_ids: user.roles.map(r => r.id),
      });
    } else {
      setEditingUser(null);
      resetUserForm();
    }
    setShowUserModal(true);
  };

  // Role CRUD operations
  const handleCreateRole = async () => {
    try {
      await api.roles.create(roleForm);
      showSuccess('Role created successfully');
      setShowRoleModal(false);
      resetRoleForm();
      const res = await api.roles.list();
      setRoles(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create role');
    }
  };

  const handleUpdateRole = async () => {
    if (!editingRole) return;
    try {
      await api.roles.update(editingRole.id, {
        name: roleForm.name,
        description: roleForm.description,
        edit_mode_enabled: roleForm.edit_mode_enabled,
      });
      await api.roles.setOperations(editingRole.id, {
        operations: roleForm.operations || [],
      });
      showSuccess('Role updated successfully');
      setShowRoleModal(false);
      setEditingRole(null);
      resetRoleForm();
      const res = await api.roles.list();
      setRoles(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update role');
    }
  };

  const handleDeleteRole = async (roleId: number) => {
    if (!confirm('Are you sure you want to delete this role?')) return;
    try {
      await api.roles.delete(roleId);
      showSuccess('Role deleted successfully');
      const res = await api.roles.list();
      setRoles(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete role');
    }
  };

  const resetRoleForm = () => {
    setRoleForm({
      name: '',
      description: '',
      edit_mode_enabled: false,
      operations: [],
    });
  };

  const openRoleModal = (role?: Role) => {
    if (role) {
      setEditingRole(role);
      setRoleForm({
        name: role.name,
        description: role.description || '',
        edit_mode_enabled: role.edit_mode_enabled,
        operations: role.operations || [],
      });
    } else {
      setEditingRole(null);
      resetRoleForm();
    }
    setShowRoleModal(true);
  };

  // Toggle edit mode
  const handleToggleEditMode = async () => {
    try {
      const newEditMode = !editMode;
      await api.security.setEditMode(newEditMode);
      setEditMode(newEditMode);
      showSuccess(`Edit mode ${newEditMode ? 'enabled' : 'disabled'} successfully`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to toggle edit mode');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Security Settings</h2>
          <p className="text-gray-600">
            Manage users, roles, and security configuration for the MCP server
          </p>
        </div>

        {/* Error/Success Messages */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
            {error}
            <button onClick={() => setError(null)} className="float-right hover:text-red-900">&times;</button>
          </div>
        )}
        {success && (
          <div className="mb-6 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-md">
            {success}
          </div>
        )}

        {/* Tabs */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="-mb-px flex space-x-8">
            {[
              { id: 'users' as TabType, label: 'Users', icon: 'M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z' },
              { id: 'roles' as TabType, label: 'Roles', icon: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z' },
              { id: 'settings' as TabType, label: 'Settings', icon: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center py-4 px-1 border-b-2 text-sm font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={tab.icon} />
                </svg>
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
            <p className="mt-2 text-gray-600">Loading...</p>
          </div>
        ) : (
          <>
            {/* Users Tab */}
            {activeTab === 'users' && (
              <div className="space-y-6">
                <div className="flex justify-between items-center">
                  <h3 className="text-lg font-semibold text-gray-900">User Management</h3>
                  <button
                    onClick={() => openUserModal()}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition flex items-center"
                  >
                    <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                    </svg>
                    Add User
                  </button>
                </div>

                <div className="bg-white rounded-lg overflow-hidden border border-gray-200 shadow">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Username</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Roles</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Edit Mode</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">API Token</th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {users.map((user) => (
                        <tr key={user.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center">
                              <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-medium">
                                {user.username[0].toUpperCase()}
                              </div>
                              <div className="ml-3">
                                <p className="text-sm font-medium text-gray-900">{user.username}</p>
                                {user.is_superuser && (
                                  <span className="text-xs text-yellow-600">Superuser</span>
                                )}
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                            {user.email || '-'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex flex-wrap gap-1">
                              {user.roles.map((role) => (
                                <span key={role.id} className="px-2 py-1 text-xs rounded bg-gray-100 text-gray-700">
                                  {role.name}
                                </span>
                              ))}
                              {user.roles.length === 0 && <span className="text-gray-400 text-sm">No roles</span>}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-2 py-1 text-xs rounded ${user.has_edit_mode ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                              {user.has_edit_mode ? 'Enabled' : 'Disabled'}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-2 py-1 text-xs rounded ${user.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                              {user.is_active ? 'Active' : 'Inactive'}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <button
                              onClick={() => handleRegenerateToken(user)}
                              className="px-3 py-1 text-xs bg-purple-100 text-purple-700 rounded hover:bg-purple-200 flex items-center"
                            >
                              <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                              </svg>
                              Generate
                            </button>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                            <button onClick={() => openUserModal(user)} className="text-blue-600 hover:text-blue-800 mr-3">Edit</button>
                            <button onClick={() => handleDeleteUser(user.id)} className="text-red-600 hover:text-red-800">Delete</button>
                          </td>
                        </tr>
                      ))}
                      {users.length === 0 && (
                        <tr>
                          <td colSpan={7} className="px-6 py-8 text-center text-gray-500">
                            No users found. Click "Add User" to create one.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Roles Tab */}
            {activeTab === 'roles' && (
              <div className="space-y-6">
                <div className="flex justify-between items-center">
                  <h3 className="text-lg font-semibold text-gray-900">Role Management</h3>
                  <button
                    onClick={() => openRoleModal()}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition flex items-center"
                  >
                    <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                    </svg>
                    Add Role
                  </button>
                </div>

                <div className="grid gap-4">
                  {roles.map((role) => (
                    <div key={role.id} className="bg-white rounded-lg p-6 border border-gray-200 shadow">
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="flex items-center space-x-2">
                            <h4 className="text-lg font-medium text-gray-900">{role.name}</h4>
                            {role.is_system_role && (
                              <span className="px-2 py-1 text-xs bg-yellow-100 text-yellow-700 rounded">System</span>
                            )}
                            {role.edit_mode_enabled && (
                              <span className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded">Edit Mode</span>
                            )}
                          </div>
                          <p className="text-gray-600 text-sm mt-1">{role.description || 'No description'}</p>
                          <p className="text-gray-500 text-xs mt-2">
                            {role.operations_count} operations assigned
                          </p>
                        </div>
                        <div className="flex space-x-2">
                          <button
                            onClick={() => openRoleModal(role)}
                            className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                          >
                            Edit
                          </button>
                          {!role.is_system_role && (
                            <button
                              onClick={() => handleDeleteRole(role.id)}
                              className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200"
                            >
                              Delete
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                  {roles.length === 0 && (
                    <div className="text-center py-8 text-gray-500">
                      No roles found. Click "Add Role" to create one.
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Settings Tab */}
            {activeTab === 'settings' && (
              <div className="space-y-6">
                {/* Global Edit Mode Toggle */}
                <div className="bg-white rounded-lg p-6 border border-gray-200 shadow">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">Global Edit Mode</h3>
                      <p className="text-sm text-gray-600">
                        Enable or disable write operations on Nexus Dashboard clusters globally.
                        This affects users without specific role-based edit permissions.
                      </p>
                      <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-md">
                        <div className="flex">
                          <svg className="h-5 w-5 text-yellow-500 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                          </svg>
                          <div>
                            <p className="text-sm font-medium text-yellow-800">Warning</p>
                            <p className="text-sm text-yellow-700 mt-1">
                              Enabling edit mode allows write operations that can modify your Nexus Dashboard configuration.
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="ml-6">
                      <button
                        onClick={handleToggleEditMode}
                        className={`relative inline-flex h-8 w-14 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                          editMode ? 'bg-blue-600' : 'bg-gray-200'
                        }`}
                        role="switch"
                        aria-checked={editMode}
                      >
                        <span
                          className={`pointer-events-none inline-block h-7 w-7 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                            editMode ? 'translate-x-6' : 'translate-x-0'
                          }`}
                        />
                      </button>
                      <p className="mt-2 text-sm font-medium text-gray-700 text-center">
                        {editMode ? 'Enabled' : 'Disabled'}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Configuration Summary */}
                <div className="bg-white rounded-lg p-6 border border-gray-200 shadow">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Configuration Summary</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="border-l-4 border-blue-500 pl-4">
                      <p className="text-sm font-medium text-gray-500">Global Edit Mode</p>
                      <p className="text-2xl font-bold text-gray-900 mt-1">
                        {editMode ? 'Enabled' : 'Disabled'}
                      </p>
                    </div>
                    <div className="border-l-4 border-green-500 pl-4">
                      <p className="text-sm font-medium text-gray-500">Total Users</p>
                      <p className="text-2xl font-bold text-gray-900 mt-1">{users.length}</p>
                    </div>
                    <div className="border-l-4 border-purple-500 pl-4">
                      <p className="text-sm font-medium text-gray-500">Total Roles</p>
                      <p className="text-2xl font-bold text-gray-900 mt-1">{roles.length}</p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </>
        )}

        {/* User Modal */}
        {showUserModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-md border border-gray-200 shadow-xl">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                {editingUser ? 'Edit User' : 'Create User'}
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
                  <input
                    type="text"
                    value={userForm.username}
                    onChange={(e) => setUserForm({ ...userForm, username: e.target.value })}
                    disabled={!!editingUser}
                    className="w-full px-3 py-2 bg-white border border-gray-300 rounded-md text-gray-900 disabled:opacity-50 disabled:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Password {editingUser && '(leave empty to keep current)'}
                  </label>
                  <input
                    type="password"
                    value={userForm.password}
                    onChange={(e) => setUserForm({ ...userForm, password: e.target.value })}
                    className="w-full px-3 py-2 bg-white border border-gray-300 rounded-md text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                  <input
                    type="email"
                    value={userForm.email}
                    onChange={(e) => setUserForm({ ...userForm, email: e.target.value })}
                    className="w-full px-3 py-2 bg-white border border-gray-300 rounded-md text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Display Name</label>
                  <input
                    type="text"
                    value={userForm.display_name}
                    onChange={(e) => setUserForm({ ...userForm, display_name: e.target.value })}
                    className="w-full px-3 py-2 bg-white border border-gray-300 rounded-md text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Roles</label>
                  <div className="space-y-2 max-h-32 overflow-y-auto border border-gray-200 rounded-md p-2">
                    {roles.map((role) => (
                      <label key={role.id} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={userForm.role_ids.includes(role.id)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setUserForm({ ...userForm, role_ids: [...userForm.role_ids, role.id] });
                            } else {
                              setUserForm({ ...userForm, role_ids: userForm.role_ids.filter(id => id !== role.id) });
                            }
                          }}
                          className="mr-2 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="text-sm text-gray-700">{role.name}</span>
                      </label>
                    ))}
                  </div>
                </div>
                <div>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={userForm.is_superuser}
                      onChange={(e) => setUserForm({ ...userForm, is_superuser: e.target.checked })}
                      className="mr-2 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-700">Superuser (full access)</span>
                  </label>
                </div>
              </div>
              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => { setShowUserModal(false); setEditingUser(null); resetUserForm(); }}
                  className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 border border-gray-300"
                >
                  Cancel
                </button>
                <button
                  onClick={editingUser ? handleUpdateUser : handleCreateUser}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  {editingUser ? 'Save Changes' : 'Create User'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Role Modal */}
        {showRoleModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-2xl border border-gray-200 shadow-xl max-h-[90vh] overflow-y-auto">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                {editingRole ? 'Edit Role' : 'Create Role'}
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Role Name</label>
                  <input
                    type="text"
                    value={roleForm.name}
                    onChange={(e) => setRoleForm({ ...roleForm, name: e.target.value })}
                    disabled={editingRole?.is_system_role}
                    className="w-full px-3 py-2 bg-white border border-gray-300 rounded-md text-gray-900 disabled:opacity-50 disabled:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                  <textarea
                    value={roleForm.description}
                    onChange={(e) => setRoleForm({ ...roleForm, description: e.target.value })}
                    rows={2}
                    className="w-full px-3 py-2 bg-white border border-gray-300 rounded-md text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={roleForm.edit_mode_enabled}
                      onChange={(e) => setRoleForm({ ...roleForm, edit_mode_enabled: e.target.checked })}
                      className="mr-2 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-700">Enable Edit Mode for this role</span>
                  </label>
                  <p className="text-xs text-gray-500 mt-1">Users with this role can perform write operations</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Allowed Operations</label>
                  <SearchableOperationsDropdown
                    selectedOperations={roleForm.operations || []}
                    onChange={(ops) => setRoleForm({ ...roleForm, operations: ops })}
                  />
                </div>
              </div>
              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => { setShowRoleModal(false); setEditingRole(null); resetRoleForm(); }}
                  className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 border border-gray-300"
                >
                  Cancel
                </button>
                <button
                  onClick={editingRole ? handleUpdateRole : handleCreateRole}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  {editingRole ? 'Save Changes' : 'Create Role'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* API Token Modal */}
        {showTokenModal && generatedToken && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-lg border border-gray-200 shadow-xl">
              <div className="flex items-center mb-4">
                <div className="h-10 w-10 rounded-full bg-purple-100 flex items-center justify-center mr-3">
                  <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">API Token Generated</h3>
                  <p className="text-sm text-gray-500">For user: {tokenUsername}</p>
                </div>
              </div>

              <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3 mb-4">
                <div className="flex">
                  <svg className="h-5 w-5 text-yellow-500 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  <p className="text-sm text-yellow-700">
                    Copy this token now. It won't be shown again!
                  </p>
                </div>
              </div>

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">API Token</label>
                <div className="flex">
                  <input
                    type="text"
                    readOnly
                    value={generatedToken}
                    className="flex-1 px-3 py-2 bg-gray-50 border border-gray-300 rounded-l-md text-gray-900 font-mono text-sm"
                  />
                  <button
                    onClick={() => copyToClipboard(generatedToken)}
                    className="px-4 py-2 bg-blue-600 text-white rounded-r-md hover:bg-blue-700 flex items-center"
                  >
                    <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
                    </svg>
                    Copy
                  </button>
                </div>
              </div>

              <div className="bg-gray-50 border border-gray-200 rounded-md p-3 mb-4">
                <p className="text-sm font-medium text-gray-700 mb-2">Claude Desktop Configuration:</p>
                <pre className="text-xs bg-gray-900 text-green-400 p-3 rounded overflow-x-auto">
{`{
  "mcpServers": {
    "nexus-dashboard": {
      "command": "npx",
      "args": ["-y", "mcp-remote",
        "http://<host>:8002/mcp/sse"],
      "env": {
        "API_TOKEN": "${generatedToken}"
      }
    }
  }
}`}
                </pre>
              </div>

              <div className="flex justify-end">
                <button
                  onClick={() => { setShowTokenModal(false); setGeneratedToken(null); setTokenUsername(''); }}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  Done
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
