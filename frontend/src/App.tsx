import { Route, Routes } from 'react-router'
import { RequireAuth } from './auth/RequireAuth'
import { Layout } from './components/Layout'
import { AdminPage } from './pages/AdminPage'
import { AuthorPage } from './pages/AuthorPage'
import { EditorPage } from './pages/EditorPage'
import { HomePage } from './pages/HomePage'
import { LoginPage } from './pages/LoginPage'
import { MyPostsPage } from './pages/MyPostsPage'
import { NotFoundPage } from './pages/PlaceholderPage'
import { PostPage } from './pages/PostPage'
import { RegisterPage } from './pages/RegisterPage'
import { SearchPage } from './pages/SearchPage'

export function App() {
  return (
    <Routes>
      {/* Every page shares the top bar and sidebar; <Outlet /> in Layout shows the page */}
      <Route element={<Layout />}>
        <Route index element={<HomePage />} />
        <Route path="login" element={<LoginPage />} />
        <Route path="register" element={<RegisterPage />} />
        <Route path="p/:slug" element={<PostPage />} />
        <Route path="u/:username" element={<AuthorPage />} />
        <Route path="search" element={<SearchPage />} />

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
              <AdminPage section="users" />
            </RequireAuth>
          }
        />
        <Route
          path="admin/audit"
          element={
            <RequireAuth role="admin">
              <AdminPage section="audit" />
            </RequireAuth>
          }
        />

        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  )
}
