import { Route, Routes } from 'react-router'
import { RequireAuth } from './auth/RequireAuth'
import { Layout } from './components/Layout'
import { EditorPage } from './pages/EditorPage'
import { HomePage } from './pages/HomePage'
import { LoginPage } from './pages/LoginPage'
import { MyPostsPage } from './pages/MyPostsPage'
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
              <EditorPage />
            </RequireAuth>
          }
        />
        <Route
          path="edit/:slug"
          element={
            <RequireAuth>
              <EditorPage />
            </RequireAuth>
          }
        />
        <Route
          path="me/posts"
          element={
            <RequireAuth>
              <MyPostsPage />
            </RequireAuth>
          }
        />
        <Route
          path="me/drafts"
          element={
            <RequireAuth>
              <MyPostsPage drafts />
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
