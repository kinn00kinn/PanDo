// frontend/src/app/api/posts/route.ts
import { createClient } from "@supabase/supabase-js";
import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth/next";

// frontend/src/app/api/auth/[...nextauth]/route.ts

import NextAuth from "next-auth";
// ★ 変更：インポート先を新しい auth.ts に変更
import { authOptions } from "@/app/lib/auth"; 




export const dynamic = "force-dynamic";

// ★★★
// このAPIは、ログイン中ユーザーの「いいね」状態や「コメント投稿者」の情報を
// RLSをバイパスして取得する必要があるため、*サービスロールキー* を使います。
// .env.local の SUPABASE_SERVICE_ROLE_KEY が必須です。
// ★★★
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!supabaseUrl || !supabaseServiceKey) {
  throw new Error(
    "Supabase URL and Service Role Key must be defined for API routes"
  );
}

// サービスロールキーでSupaClientを初期化
const supabase = createClient(supabaseUrl, supabaseServiceKey, {
  auth: {
    // ユーザーRLEを強制しない
    autoRefreshToken: false,
    persistSession: false,
  },
});

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);

    // --- 1. セッションの取得 (ログインしていなくてもOK) ---
    // @ts-ignore
    const session = await getServerSession(authOptions);
    // ログインしていれば user_id をRPCに渡す
    const requesting_user_id = session?.user?.id || null;

    // --- 2. クエリパラメータの取得 ---
    const page = parseInt(searchParams.get("page") || "1", 10);
    const limit = parseInt(searchParams.get("limit") || "20", 10);
    // ソートモード: 'recent' (デフォルト) または 'likes'
    const sort = searchParams.get("sort") || "recent";
    // 'my-likes' ページ用のフィルタ
    const liked_by_user = searchParams.get("liked_by_user") === "true";

    const MAX_LIMIT = 100;
    const safeLimit = Math.max(1, Math.min(limit, MAX_LIMIT));

    if (isNaN(page) || page < 1) {
      return NextResponse.json({ error: "Invalid page." }, { status: 400 });
    }

    // --- 3. RPCの呼び出し ---
    // 'get_feed_articles' (page_num, page_limit, sort_mode, requesting_user_id)

    // liked_by_user=true の場合、RPCではなく直接 user_likes をJOINするクエリを組む
    // (RPCを複雑化させないため)
    if (liked_by_user && requesting_user_id) {
      const offset = (page - 1) * safeLimit;

      // ★ 'my-likes' 専用クエリ
      // (get_feed_articles RPC とほぼ同じロジックだが、
      //  INNER JOIN user_likes で絞り込む点が異なる)
      const { data, error, count } = await supabase
            .from('articles')
            .select(`
                id, title, article_url, published_at, source_name, image_url, like_num,
                is_liked:user_likes!inner(user_id),
                comments ( id, created_at, text, user_id, user:users(id, name, image) )
            `, { count: 'exact' }) // ★ 'user:users' の中身を 'image' に簡略化
            .eq('user_likes.user_id', requesting_user_id)
        .order("created_at", { foreignTable: "user_likes", ascending: false }) // いいねした順
        .limit(3, { foreignTable: "comments" }) // コメントは3件まで
        .order("created_at", { foreignTable: "comments", ascending: false }) // コメントは新しい順
        .range(offset, offset + safeLimit - 1);

      if (error) throw error;

      // is_liked が配列[]で返ってくるのでbooleanに変換
      const articles = data.map((a) => ({
        ...a,
        is_liked: Array.isArray(a.is_liked) && a.is_liked.length > 0,
      }));
      const hasMore = count ? offset + articles.length < count : false;
      return NextResponse.json({ articles, total: count, hasMore });
    } else {
      // ★ 通常のタイムライン (RPC呼び出し)
      const { data, error } = await supabase.rpc("get_feed_articles", {
        page_num: page,
        page_limit: safeLimit,
        sort_mode: sort === "likes" ? "likes" : "recent", // 'recent' をデフォルトに
        requesting_user_id: requesting_user_id,
      });

      if (error) {
        console.error("Supabase RPC error:", error);
        throw new Error(error.message);
      }

      // RPCはhasMoreを返さないので、件数がlimit未満かで判定
      const hasMore = data.length === safeLimit;

      return NextResponse.json({
        articles: data,
        total: null, // RPCでは総数を取得していない
        hasMore: hasMore,
      });
    }
  } catch (error) {
    console.error("API route error:", error);
    const errorMessage =
      error instanceof Error ? error.message : "Internal Server Error";
    return NextResponse.json({ error: errorMessage }, { status: 500 });
  }
}
