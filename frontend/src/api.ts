import axios from "axios";

const baseURL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

export const api = axios.create({ baseURL });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("orthoreco_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (resp) => resp,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("orthoreco_token");
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  },
);

export type PatientTableRow = {
  id: number;
  patient_id: string;
  first_name: string;
  last_name: string;
  email: string;
  gender: string;
  date_of_birth: string | null;
  surgery_type: string;
  surgery_side: string;
  surgery_date: string | null;
  days_since_surgery: number | null;
  total_gait_records: number;
  total_reports: number;
  last_gait_date: string | null;
  last_report_date: string | null;
  latest_recovery_score: number | null;
  latest_recovery_status: string | null;
};

export type GaitSeriesPoint = {
  record_date: string;
  step_count: number;
  walking_speed: number | null;
  cadence: number | null;
  distance: number | null;
  active_minutes: number | null;
};

export type ReportSeriesPoint = {
  report_date: string;
  pain_score: number;
  stiffness_score: number;
  walking_difficulty: number;
  confidence_score: number;
  swelling_flag: boolean;
  exercise_completed: boolean;
  recovery_score: number;
  recovery_status: string;
};

export type PatientDetail = {
  profile: PatientTableRow;
  recent_gait: GaitSeriesPoint[];
  recent_reports: ReportSeriesPoint[];
};

export type Analytics = {
  total_patients: number;
  total_clinicians: number;
  total_gait_records: number;
  total_reports: number;
  average_recovery_score: number;
  surgery_type_breakdown: { surgery_type: string; patient_count: number }[];
  recovery_distribution: { bucket: string; patient_count: number }[];
  top_risk_patients: {
    patient_id: string;
    first_name: string;
    last_name: string;
    surgery_type: string;
    latest_recovery_score: number;
    latest_recovery_status: string;
    last_report_date: string;
  }[];
  patients_active_last_7_days: number;
};

export async function login(email: string, password: string) {
  const form = new URLSearchParams();
  form.append("username", email);
  form.append("password", password);
  const { data } = await api.post<{ access_token: string; token_type: string }>(
    "/auth/login",
    form,
    { headers: { "Content-Type": "application/x-www-form-urlencoded" } },
  );
  localStorage.setItem("orthoreco_token", data.access_token);
  return data.access_token;
}

export type ClinicianRegisterPayload = {
  first_name: string;
  last_name: string;
  gender: string;
  license_id: string;
  email: string;
  password: string;
};

export async function registerClinician(payload: ClinicianRegisterPayload) {
  const { data } = await api.post("/auth/register-clinician", payload);
  return data;
}

export type Appointment = {
  id: number;
  doctor_id: number;
  doctor_name: string;
  doctor_email: string;
  patient_id: number;
  patient_patient_id: string;
  patient_first_name: string;
  patient_last_name: string;
  patient_email: string;
  scheduled_for: string;
  location: string | null;
  notes: string | null;
  status: string;
  invitation_sent: boolean;
  created_at: string;
};

export type AppointmentCreatePayload = {
  patient_id: string;
  scheduled_for: string; // ISO datetime
  location?: string;
  notes?: string;
  send_email?: boolean;
};

export async function createAppointment(payload: AppointmentCreatePayload) {
  const { data } = await api.post<Appointment>("/appointments/", payload);
  return data;
}

export async function listMyAppointments() {
  const { data } = await api.get<Appointment[]>("/appointments/me");
  return data;
}

export type PatientNote = {
  id: number;
  doctor_id: number;
  doctor_name: string;
  patient_id: number;
  patient_patient_id: string;
  body: string;
  sent_email: boolean;
  created_at: string;
};

export type PatientNoteCreatePayload = {
  patient_id: string;
  body: string;
  send_email?: boolean;
};

export async function createPatientNote(payload: PatientNoteCreatePayload) {
  const { data } = await api.post<PatientNote>("/patient-notes/", payload);
  return data;
}

export async function listPatientNotes(patientId: string) {
  const { data } = await api.get<PatientNote[]>(
    `/patient-notes/patient/${encodeURIComponent(patientId)}`,
  );
  return data;
}

export function logout() {
  localStorage.removeItem("orthoreco_token");
}

export function isLoggedIn() {
  return Boolean(localStorage.getItem("orthoreco_token"));
}
