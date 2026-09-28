import { Route } from 'react-router'
import { RequireAuth } from './auth/RequireAuth'
import { Layout } from './components/Layout'
import { AdminPage } from './pages/AdminPage'
import { AuthorPage } from './pages/AuthorPage'
import { EditorRoute } from './pages/EditorRoute'
import { HomePage } from './pages/HomePage'
import { LoginPage } from './pages/LoginPage'
import { MyPostsPage } from './pages/MyPostsPage'
import { NotFoundPage } from './pages/PlaceholderPage'
import { PostPage } from './pages/PostPage'
import { RegisterPage } from './pages/RegisterPage'
import { SearchPage } from './pages/SearchPage'
import { TopicPage } from './pages/TopicPage'

/** Every page, for createRoutesFromElements in main.tsx */
export const routes = (
  // Every page shares the top bar and sidebar; <Outlet /> in Layout shows the page
  <Route element={<Layout />}>
    <Route index element={<HomePage />} />
    <Route path="login" element={<LoginPage />} />
    <Route path="register" element={<RegisterPage />} />
    <Route path="p/:slug" element={<PostPage />} />
    <Route path="u/:username" element={<AuthorPage />} />
    <Route path="t/:slug" element={<TopicPage />} />
    <Route path="search" element={<SearchPage />} />

    <Route path="write" element={<EditorRoute />} />
    <Route path="edit/:slug" element={<EditorRoute />} />
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
)
