/*
frontend/src/app/links/creator/page.tsx (新規作成)
*/
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import Image from "next/image";

const CreatorPage = () => {
  return (
    <div className="flex justify-center bg-white text-black">
      <div className="w-full max-w-xl">
        {/* ヘッダー */}
        <header className="sticky top-0 z-10 bg-white/90 backdrop-blur-sm p-2 border-b-2 border-black flex items-center space-x-4">
          <Link
            href="/links"
            className="p-2 hover:bg-gray-100 rounded-full"
            aria-label="戻る"
          >
            <ArrowLeft size={20} />
          </Link>
          <div>
            <h1 className="text-xl font-bold">クリエイター紹介</h1>
          </div>
        </header>

        {/* メインコンテンツ */}
        <main className="border-x-2 border-b-2 border-black p-6">
          <div className="space-y-8">
            {/* クリエイター プロフィールセクション */}
            <section className="flex flex-col items-center text-center">
              {/* ★ 要設定: 
                ここにクリエイターのアイコン画像パスを設定します。
                (例: /images/creator_avatar.png)
                設定が完了したら、下のプレースホルダー(<svg>)は削除してください。
              */}
              <div className="w-32 h-32 rounded-full border-4 border-black overflow-hidden bg-gray-100 mb-4 flex items-center justify-center">
                {
                  <Image
                    src="/icon/creater.jpg"
                    alt="Creator Avatar"
                    width={128}
                    height={128}
                    className="object-cover w-full h-full"
                  />
                }
                {/* --- 以下はプレースホルダー --- */}

                {/* --- プレースホルダーここまで --- */}
              </div>

              <h2 className="text-2xl font-bold">haharman</h2>
              <p className="text-sm text-gray-500">
                [ドット絵アイコン / @_haharman]
              </p>
            </section>

            {/* 自己紹介セクション */}
            <section>
              <h3 className="text-xl font-bold mb-2">ごあいさつ</h3>
              <p className="text-gray-800 leading-relaxed">
                ドット絵を担当した@_Haharmanです！
                <br />
                <br />
                最小サイズでかわいらしいパンダを表現できたのではないかと満足しています。
                <br />
                普段はXに風景を投稿したりドット絵のイベントに出展したりしておりますので是非チェックしてみてください！
              </p>
            </section>

            {/* リンク集セクション */}
            <section>
              <h3 className="text-xl font-bold mb-3 text-center">
                クリエイターの活動
              </h3>
              <div className="flex justify-center gap-4 flex-wrap">
                {/* テンプレート: X (Twitter) */}
                <a
                  href="https://x.com/_haharman" // ★ 要変更
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-block text-white bg-black border-2 border-black px-4 py-2 rounded-full hover:bg-gray-800 transition-colors"
                >
                  X (Twitter)
                </a>
              </div>
            </section>
          </div>
        </main>
      </div>
    </div>
  );
};

export default CreatorPage;
