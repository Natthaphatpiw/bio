import { NextResponse } from 'next/server';

// In production, use Supabase client
// import { createServerClient } from '@/lib/supabase';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { session_id, result, overall_status } = body;

    if (!session_id) {
      return NextResponse.json(
        { error: 'session_id is required' },
        { status: 400 }
      );
    }

    // In production, update Supabase database
    /*
    const supabase = createServerClient();

    const { data, error } = await supabase
      .from('verification_sessions')
      .update({
        status: overall_status,
        result: result,
      })
      .eq('id', session_id)
      .select()
      .single();

    if (error) {
      return NextResponse.json({ error: error.message }, { status: 500 });
    }

    // Send webhook if configured
    if (data.webhook_url) {
      try {
        await fetch(data.webhook_url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            event: 'verification.completed',
            session_id: session_id,
            status: overall_status,
            result: result,
            timestamp: new Date().toISOString(),
          }),
        });
      } catch (webhookError) {
        console.error('Webhook failed:', webhookError);
      }
    }
    */

    // For demo, just log and return success
    console.log('Verification callback received:', {
      session_id,
      overall_status,
      result,
    });

    return NextResponse.json({
      success: true,
      session_id,
      status: overall_status,
      message: 'Verification result recorded',
    });
  } catch (error) {
    console.error('Callback error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

// Health check
export async function GET() {
  return NextResponse.json({
    status: 'ok',
    service: 'BioGuard Callback API',
    timestamp: new Date().toISOString(),
  });
}
