import { NextRequest, NextResponse } from 'next/server';
import { isItsIdValid, isMajlisIdValid } from '@/lib/cache';
import { createSession, isUserAlreadyLoggedIn, removeExistingUserSessions } from '@/lib/session';
import { isValidId } from '@/lib/utils';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { user_id, selected_role, force_login } = body;

    if (!user_id || !isValidId(user_id)) {
      return NextResponse.json(
        { success: false, error: 'Please enter a valid 8-digit ID' },
        { status: 400 }
      );
    }

    // Asbaaq (ITS) module temporarily disabled — only check Majlis
    const isMajlis = await isMajlisIdValid(user_id);

    if (!isMajlis) {
      return NextResponse.json(
        { success: false, error: 'Access denied. Your ID is not authorized.' },
        { status: 403 }
      );
    }

    // Determine user type — only Majlis active
    const userType: 'its' | 'majlis' = 'majlis';
    const redirectPath = '/majlis';

    // Check device restriction
    const alreadyLoggedIn = await isUserAlreadyLoggedIn(user_id, userType);
    if (alreadyLoggedIn) {
      if (force_login) {
        // User chose to logout from all devices and login here
        await removeExistingUserSessions(user_id, userType);
      } else {
        return NextResponse.json(
          { success: false, already_logged_in: true, error: 'This ID is already logged in on another device.' },
          { status: 409 }
        );
      }
    }

    // Create session
    const token = await createSession(user_id, userType);

    const response = NextResponse.json({
      success: true,
      redirect: redirectPath,
    });

    // Set httpOnly cookie
    response.cookies.set('session_token', token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 86400, // 24 hours
      path: '/',
    });

    return response;
  } catch (error) {
    console.error('Login error:', error);
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    );
  }
}
