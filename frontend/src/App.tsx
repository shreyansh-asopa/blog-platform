import { Route, Routes } from 'react-router'
import { RequireAuth } from './auth/RequireAuth'
import { Layout } from './components/Layout'
import { HomePage } from './pages/HomePage'
import { LoginPage } from './pages/LoginPage'
import { NotFoundPage, PlaceholderPage } from './pages/PlaceholderPage'
import { PostPage } from './pages/PostPage'
import { RegisterPage } from './pages/RegisterPage'

export function App() {
  return (
    <Routes>
      {/* Every page shares the top bar and sidebar; <Outlet /> in Layout shows the page */}
      <Route element={<Layout />}>
        <Route index element={<HomePage />} />
        <Route path="login" element={<LoginPage />} />
        <Route path="register" element={<RegisterPage />} />
        <Route path="p/:slug" element={<PostPage />} />

        <Route
          path="write"
          element={
            <RequireAuth>
              <PlaceholderPage title="Write a post" />
            </RequireAuth>
          }
        />
        <Route
          path="me/posts"
          element={
            <RequireAuth>
              <PlaceholderPage title="My posts" />
            </RequireAuth>
          }
        />
        <Route
          path="me/drafts"
          element={
            <RequireAuth>
              <PlaceholderPage title="Drafts" />
            </RequireAuth>
          }
        />
        <Route
          path="admin"
          element={
            <RequireAuth role="admin">
              <PlaceholderPage title="Admin" />
            </RequireAuth>
          }
        />

        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  )
}
