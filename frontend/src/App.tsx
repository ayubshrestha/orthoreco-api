import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
} from "react-router-dom";
import { LoginPage } from "./pages/Login";
import { RegisterDoctorPage } from "./pages/RegisterDoctor";
import { OverviewPage } from "./pages/Overview";
import { PatientsPage } from "./pages/Patients";
import { PatientDetailPage } from "./pages/PatientDetail";
import { AppointmentsPage } from "./pages/Appointments";
import { Layout } from "./components/Layout";
import { isLoggedIn } from "./api";

function RequireAuth({ children }: { children: React.ReactElement }) {
  return isLoggedIn() ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register-doctor" element={<RegisterDoctorPage />} />
        <Route
          element={
            <RequireAuth>
              <Layout />
            </RequireAuth>
          }
        >
          <Route path="/" element={<OverviewPage />} />
          <Route path="/patients" element={<PatientsPage />} />
          <Route
            path="/patients/:patientId"
            element={<PatientDetailPage />}
          />
          <Route path="/appointments" element={<AppointmentsPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
