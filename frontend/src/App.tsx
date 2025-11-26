import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Login } from './features/auth/Login';
import { Register } from './features/auth/Register';
import { WorldList } from './features/world/WorldList';
import { WorldView } from './features/world/WorldView';
import { IdeaInjection } from './features/world/IdeaInjection';
import { ProtectedRoute } from './components/layout/ProtectedRoute';
import { DashboardLayout } from './components/layout/DashboardLayout';

const queryClient = new QueryClient();

const DashboardWrapper: React.FC = () => (
  <DashboardLayout>
    <Outlet />
  </DashboardLayout>
);

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          
          {/* Protected Routes */}
          <Route element={<ProtectedRoute />}>
            <Route element={<DashboardWrapper />}>
              <Route path="/dashboard" element={<WorldList />} />
              <Route path="/worlds" element={<WorldList />} />
              <Route path="/worlds/:worldId" element={<WorldView />} />
              <Route path="/worlds/:worldId/inject" element={<IdeaInjection />} />
              
              {/* Default redirect */}
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
            </Route>
          </Route>
          
          {/* Fallback */}
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
