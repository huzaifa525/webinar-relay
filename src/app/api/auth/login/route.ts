import { NextRequest, NextResponse } from 'next/server';
import { isItsIdValid, isMajlisIdValid } from '@/lib/cache';
import { createSession, isUserAlreadyLoggedIn } from '@/lib/session';
import { isValidId } from '@/lib/utils';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { user_id, selected_role } = body;

    if (!user_id || !isValidId(user_id)) {
      return NextResponse.json(
        { success: false, error: 'Please enter a valid 8-digit ID' },
        { status: 400 }
      );
    }

    const [isIts, isMajlis] = await Promise.all([
      isItsIdValid(user_id),
      isMajlisIdValid(user_id),
    ]);

    // If neither found
    if (!isIts && !isMajlis) {
      return NextResponse.json(
        { success: false, error: 'Access denied. Your ID is not authorized.' },
        { status: 403 }
      );
    }

    // Dual-access: both ITS and Majlis - need role selection
    if (isIts && isMajlis && !selected_role) {
      return NextResponse.json({
        success: true,
        redirect: '/select-role',
        dual_access: true,
      });
    }

    // Determine user type
    let userType: 'its' | 'majlis';
    let redirectPath: string;

    if (selected_role) {
      // Role was selected (dual-access flow)
      userType = selected_role as 'its' | 'majlis';
      redirectPath = userType === 'its' ? '/webinar' : '/majlis';
    } else if (isIts) {
      userType = 'its';
      redirectPath = '/webinar';
    } else {
      userType = 'majlis';
      redirectPath = '/majlis';
    }

    // Check device restriction
    const alreadyLoggedIn = await isUserAlreadyLoggedIn(user_id, userType);
    if (alreadyLoggedIn) {
      return NextResponse.json(
        { success: false, error: 'This ID is already logged in on another device. Please logout first or use force logout.' },
        { status: 409 }
      );
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
