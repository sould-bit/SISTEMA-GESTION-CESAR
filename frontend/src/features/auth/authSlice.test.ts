import { describe, it, expect } from 'vitest';
import authReducer, { setCredentials, logout } from './authSlice';
import { User } from '../../types';

describe('authSlice', () => {
  const initialState = {
    user: null,
    token: null,
    isAuthenticated: false,
  };

  const mockUser: User = {
    id: 1,
    username: 'testuser',
    email: 'test@example.com',
    fullName: 'Test User',
    role: 'admin',
    companyId: 1,
  };

  it('should handle initial state', () => {
    expect(authReducer(undefined, { type: 'unknown' })).toEqual({
      user: null,
      token: null, // Depending on localStorage mock, this might vary in real app, but for unit test undefined is fine if localStorage is mocked or empty
      isAuthenticated: false,
    });
  });

  it('should handle setCredentials', () => {
    const actual = authReducer(
      initialState,
      setCredentials({ user: mockUser, token: 'fake-token' })
    );
    expect(actual.user).toEqual(mockUser);
    expect(actual.token).toEqual('fake-token');
    expect(actual.isAuthenticated).toEqual(true);
  });

  it('should handle logout', () => {
    const loggedInState = {
      user: mockUser,
      token: 'fake-token',
      isAuthenticated: true,
    };
    const actual = authReducer(loggedInState, logout());
    expect(actual).toEqual({
      user: null,
      token: null,
      isAuthenticated: false,
    });
  });
});
