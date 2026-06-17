export default function Avatar({ letter = "i", size = "h-20 w-20", text = "text-3xl" }) {
  return (
    <div className={`grid ${size} place-items-center rounded-full border-4 border-pepper bg-ash ${text} font-black`}>
      {letter}
    </div>
  );
}
