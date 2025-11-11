import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import ErrorBoundary from './components/ErrorBoundary'
import { ThemeProvider } from './contexts/ThemeContext'
import Layout from './components/Layout'
import HomePage from './pages/HomePage'
import CreateProjectPage from './pages/CreateProjectPage'
import ProjectDetailPage from './pages/ProjectDetailPage'
import ProjectsListPage from './pages/ProjectsListPage'
import SettingsPage from './pages/SettingsPage'
import TemplatesPage from './pages/TemplatesPage'

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <Router>
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#363636',
                color: '#fff',
              },
              success: {
                duration: 3000,
                iconTheme: {
                  primary: '#10b981',
                  secondary: '#fff',
                },
              },
              error: {
                duration: 5000,
                iconTheme: {
                  primary: '#ef4444',
                  secondary: '#fff',
                },
              },
            }}
          />
          <Layout>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/create" element={<CreateProjectPage />} />
              <Route path="/projects" element={<ProjectsListPage />} />
              <Route path="/projects/:projectId" element={<ProjectDetailPage />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="/templates" element={<TemplatesPage />} />
            </Routes>
          </Layout>
        </Router>
      </ThemeProvider>
    </ErrorBoundary>
  )
}

export default App
