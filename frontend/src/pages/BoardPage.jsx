import { useEffect, useState } from "react";

import { createBoardComment, fetchDailyProblem, fetchProblemBoard } from "../api/client";
import Card from "../components/Card";
import Shell from "../components/Shell";

const areaLabels = {
  reading_comprehension: "언어이해",
  reasoning_argumentation: "추리논증",
};

export default function BoardPage({ page, setPage }) {
  const [board, setBoard] = useState(null);
  const [commentDrafts, setCommentDrafts] = useState({});
  const [commentSubmittingId, setCommentSubmittingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [commentErrors, setCommentErrors] = useState({});

  useEffect(() => {
    let ignore = false;

    async function loadBoard() {
      try {
        setLoading(true);
        const daily = await fetchDailyProblem();
        const data = await fetchProblemBoard(daily.problem.id);
        if (!ignore) {
          setBoard(data);
          setError("");
        }
      } catch (err) {
        if (!ignore) {
          setBoard(null);
          setError(err.message);
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    }

    loadBoard();
    return () => {
      ignore = true;
    };
  }, []);

  const problem = board?.problem;

  async function handleCommentSubmit(postId) {
    const content = commentDrafts[postId]?.trim() ?? "";
    if (!content) {
      setCommentErrors((current) => ({ ...current, [postId]: "댓글 내용을 입력해주세요." }));
      return;
    }
    if (!problem) {
      return;
    }

    try {
      setCommentSubmittingId(postId);
      const comment = await createBoardComment({ problemId: problem.id, postId, content });
      setBoard((current) => {
        if (!current) {
          return current;
        }
        return {
          ...current,
          posts: current.posts.map((post) =>
            post.id === postId ? { ...post, comments: [...(post.comments ?? []), comment] } : post
          ),
        };
      });
      setCommentDrafts((current) => ({ ...current, [postId]: "" }));
      setCommentErrors((current) => ({ ...current, [postId]: "" }));
    } catch (err) {
      setCommentErrors((current) => ({ ...current, [postId]: err.message }));
    } finally {
      setCommentSubmittingId(null);
    }
  }

  return (
    <Shell page={page} setPage={setPage}>
      <div className="mx-auto w-full max-w-[1040px] space-y-7 px-3 py-6 lg:px-7 lg:py-8">
        <Card className="border-pepper p-7">
          <div className="mb-8 flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
            <div>
              <p className="mb-4 text-sm font-black">문제별 추론 게시판</p>
              <h2 className="text-3xl font-black">오늘의 문제를 푼 사람들의 생각</h2>
            </div>
            <button onClick={() => setPage("daily")} className="h-11 w-fit rounded-md border border-smoke px-5 text-sm font-black hover:bg-paper">
              오늘의 문제
            </button>
          </div>

          {loading && <div className="grid min-h-60 place-items-center text-lg font-black">게시판을 불러오는 중...</div>}

          {!loading && error && (
            <div className="rounded-md border border-pepper bg-paper p-6">
              <p className="text-xl font-black">아직 게시판을 볼 수 없어요.</p>
              <p className="mt-3 text-sm leading-7">
                이 문제를 제출한 뒤에 다른 사람들의 추론을 볼 수 있어요. 서버에서 스포일러 차단 규칙을 적용하고 있습니다.
              </p>
              <p className="mt-3 text-xs font-black text-[#666]">{error}</p>
            </div>
          )}

          {!loading && problem && (
            <div className="mx-auto w-fit max-w-full rounded-md border border-smoke p-5">
              <div className="mb-4 flex flex-wrap gap-3">
                <span className="rounded-md bg-ash px-4 py-2 text-xs font-black">{areaLabels[problem.area]}</span>
                <span className="rounded-md bg-ash px-4 py-2 text-xs font-black">{problem.year}학년도</span>
                <span className="rounded-md bg-ash px-4 py-2 text-xs font-black">{problem.number}번</span>
              </div>
              <p className="whitespace-pre-line break-keep text-base font-black leading-7">{problem.question_text}</p>
            </div>
          )}
        </Card>

        {!error && (
          <Card className="p-7">
            <h2 className="mb-6 text-2xl font-black">추론 게시글</h2>
            {!board?.posts?.length && !loading ? (
              <p className="rounded-md border border-smoke p-5 text-sm font-black">아직 등록된 추론 게시글이 없어요.</p>
            ) : (
              <div className="mx-auto max-w-[860px] space-y-4">
                {board?.posts.map((post) => (
                  <article key={post.id} className="rounded-md border border-smoke p-5">
                    <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                      <div>
                        <p className="text-lg font-black">{post.nickname}</p>
                        <p className="text-xs text-[#666]">{new Date(post.created_at).toLocaleString("ko-KR")}</p>
                      </div>
                      <div className="flex gap-2">
                        <span className="rounded-md bg-ash px-3 py-2 text-xs font-black">선택 {post.selected_index}번</span>
                        <span className="rounded-md bg-pepper px-3 py-2 text-xs font-black text-white">
                          {post.is_correct ? "정답" : "오답"}
                        </span>
                      </div>
                    </div>
                    <p className="whitespace-pre-line break-keep text-base leading-7">{post.content}</p>
                    <div className="mt-5 border-t border-ash pt-5">
                      <h3 className="mb-3 text-sm font-black">댓글</h3>
                      {post.comments?.length ? (
                        <div className="mb-4 space-y-3">
                          {post.comments.map((comment) => (
                            <div key={comment.id} className="rounded-md bg-paper px-4 py-3">
                              <div className="mb-2 flex flex-wrap items-center gap-2">
                                <p className="text-sm font-black">{comment.nickname}</p>
                                <p className="text-xs text-[#666]">{new Date(comment.created_at).toLocaleString("ko-KR")}</p>
                              </div>
                              <p className="whitespace-pre-line break-keep text-sm leading-6">{comment.content}</p>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="mb-4 rounded-md bg-paper px-4 py-3 text-sm font-black text-[#666]">아직 댓글이 없어요.</p>
                      )}
                      <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_120px]">
                        <textarea
                          value={commentDrafts[post.id] ?? ""}
                          onChange={(event) => setCommentDrafts((current) => ({ ...current, [post.id]: event.target.value }))}
                          className="min-h-20 w-full rounded-md border border-smoke p-3 text-sm leading-6"
                          placeholder="이 추론에 대한 댓글을 남겨보세요."
                        />
                        <button
                          type="button"
                          disabled={commentSubmittingId === post.id}
                          onClick={() => handleCommentSubmit(post.id)}
                          className="min-h-11 rounded-md bg-pepper px-4 py-3 text-sm font-black text-white hover:bg-[#444] disabled:cursor-not-allowed disabled:bg-smoke"
                        >
                          {commentSubmittingId === post.id ? "등록 중..." : "댓글 등록"}
                        </button>
                      </div>
                      {commentErrors[post.id] && (
                        <p className="mt-3 rounded-md border border-pepper bg-paper px-4 py-3 text-sm font-black">
                          {commentErrors[post.id]}
                        </p>
                      )}
                    </div>
                  </article>
                ))}
              </div>
            )}
          </Card>
        )}
      </div>
    </Shell>
  );
}
