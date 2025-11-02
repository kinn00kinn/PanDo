import Timeline from "@/app/components/Timeline";
import Image from "next/image";

export default function Home() {
  return (
    // ★ 画面全体を中央寄せにするためのラッパー
    // PCでは左右に余白ができ、スマホでは全幅になる
    <div className="flex justify-center bg-white text-black">
      {/* メインのコンテンツコンテナ (PCでの最大幅を設定) */}
      <div className="w-full max-w-xl">
        {/* ヘッダー: スケッチのデザインを忠実に再現 */}
        <header className="w-full bg-white/90 backdrop-blur-sm sticky top-0 z-10 ">
          {/* ★ 修正: 要素がImageのみになったため、flexレイアウト関連のクラスを削除 */}
          <div className="px-4 py-3 border-b-2 border-black">
            {/* ★ 修正点: 
       1. srcパスを / (publicフォルダのルート) から始まるように変更
       2. className="w-full h-auto" を追加し、親要素の幅(px-4の内側)に合わせる
      */}
            <Image
              src="/Pando_banner_1000.gif" // ★ 修正: publicフォルダからのパス
              alt="NScroller Logo"
              width={400} // アスペクト比のヒント (例: 400:40 = 10:1)
              height={40} // アスペクト比のヒント
              className="w-full h-auto" // ★ 追加: 親要素(padding適用後)の幅いっぱいに表示
              unoptimized // ★ GIF画像の場合は最適化をオフ
            />
          </div>
        </header>

        {/* タイムライン本体 (左右の境界線を追加) */}
        <main className="border-x-2 border-black">
          <Timeline />
        </main>
      </div>
    </div>
  );
}
