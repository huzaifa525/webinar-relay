export interface SessionData {
  user_type: 'its' | 'majlis';
  user_id: string;
  login_time: string;
  last_activity: string;
}

export interface WebinarSettings {
  embed_url: string;
  youtube_video_id: string;
  webinar_title: string;
  no_webinar: boolean;
}

export interface AdminStats {
  total_its: number;
  total_majlis: number;
  its_sessions: number;
  majlis_sessions: number;
  total_sessions: number;
}

export interface SessionInfo {
  token: string;
  user_id: string;
  user_type: 'its' | 'majlis';
  login_time: string;
  last_activity: string;
}

export type UserType = 'its' | 'majlis';

export type NotificationType = 'success' | 'error' | 'warning' | 'info';

export interface Notification {
  id: string;
  type: NotificationType;
  message: string;
  duration?: number;
}
