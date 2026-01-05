import { api } from '../../services/api';
import { User } from '../../types';

export const authApi = api.injectEndpoints({
  endpoints: (builder) => ({
    login: builder.mutation<{ user: User; token: string }, any>({
      query: (credentials) => ({
        url: '/auth/login',
        method: 'POST',
        body: credentials,
      }),
      async queryFn(_args, _queryApi, _extraOptions, _baseQuery) {
          // MOCK IMPLEMENTATION
          await new Promise(resolve => setTimeout(resolve, 1000));

          if (_args.username === 'admin' && _args.password === '123456') {
             return {
                 data: {
                     user: {
                         id: 1,
                         username: 'admin',
                         email: 'admin@fastops.com',
                         fullName: 'Admin User',
                         role: 'admin',
                         companyId: 1,
                         branchId: 1
                     },
                     token: 'mock-jwt-token-12345'
                 }
             }
          }
           return { error: { status: 401, data: { message: 'Invalid credentials' } } };
      }
    }),
  }),
});

export const { useLoginMutation } = authApi;
