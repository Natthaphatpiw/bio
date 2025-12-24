import { NextResponse } from 'next/server';

// In production, use Supabase client
// import { createServerClient } from '@/lib/supabase';

export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  const sessionId = params.id;

  if (!sessionId) {
    return NextResponse.json(
      { error: 'Session ID is required' },
      { status: 400 }
    );
  }

  try {
    // In production, fetch from Supabase
    /*
    const supabase = createServerClient();

    const { data, error } = await supabase
      .from('verification_sessions')
      .select('*')
      .eq('id', sessionId)
      .single();

    if (error || !data) {
      return NextResponse.json(
        { error: 'Session not found' },
        { status: 404 }
      );
    }

    return NextResponse.json(data);
    */

    // For demo, return default config
    return NextResponse.json({
      id: sessionId,
      status: 'PENDING',
      config: {
        check_emulator: true,
        light_sync: true,
        face_liveness: true,
      },
      created_at: new Date().toISOString(),
    });
  } catch (error) {
    console.error('Session fetch error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
