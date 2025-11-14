import math, random, csv, io
import streamlit as st
import numpy as np
import pandas as pd

# =======================================
#  THUẬT TOÁN SUDOKU (lấy lại từ bản Tkinter)
# =======================================

def valid_in_board(board, n, box_size, row, col, num):
    """Kiểm tra số num có hợp lệ đặt vào (row,col) trên board kích thước n"""
    for k in range(n):
        if board[row][k] == num:
            return False
        if board[k][col] == num:
            return False
    start_r = row - row % box_size
    start_c = col - col % box_size
    for i in range(box_size):
        for j in range(box_size):
            if board[start_r + i][start_c + j] == num:
                return False
    return True

def solve_backtrack(board, n, box_size):
    """Giải Sudoku — trả về True nếu giải được"""
    for r in range(n):
        for c in range(n):
            if board[r][c] == 0:
                for num in range(1, n + 1):
                    if valid_in_board(board, n, box_size, r, c, num):
                        board[r][c] = num
                        if solve_backtrack(board, n, box_size):
                            return True
                        board[r][c] = 0
                return False
    return True

def generate_full_board(n):
    """Tạo 1 board đã giải hoàn chỉnh ngẫu nhiên."""
    box_size = int(math.sqrt(n))
    board = [[0] * n for _ in range(n)]
    nums = list(range(1, n + 1))

    def helper(pos=0):
        if pos == n * n:
            return True
        r = pos // n
        c = pos % n
        random.shuffle(nums)
        for num in nums:
            if valid_in_board(board, n, box_size, r, c, num):
                board[r][c] = num
                if helper(pos + 1):
                    return True
                board[r][c] = 0
        return False

    ok = helper()
    if not ok:
        raise RuntimeError("Không tạo được board hoàn chỉnh — thử lại.")
    return board

def remove_cells_for_difficulty(board, difficulty):
    """Xóa ô theo mức độ (không kiểm tra duy nhất 1 nghiệm để nhanh)"""
    n = len(board)
    puzzle = [row[:] for row in board]
    total = n * n

    if n == 9:
        if difficulty == "Dễ":
            remove = 40
        elif difficulty == "Trung bình":
            remove = 50
        else:
            remove = 60
    elif n == 16:
        if difficulty == "Dễ":
            remove = int(total * 0.55)
        elif difficulty == "Trung bình":
            remove = int(total * 0.65)
        else:
            remove = int(total * 0.75)
    else:  # 25
        if difficulty == "Dễ":
            remove = int(total * 0.5)
        elif difficulty == "Trung bình":
            remove = int(total * 0.65)
        else:
            remove = int(total * 0.8)

    remove = min(remove, total - 1)
    cells = [(r, c) for r in range(n) for c in range(n)]
    random.shuffle(cells)
    removed = 0
    for (r, c) in cells:
        if removed >= remove:
            break
        puzzle[r][c] = 0
        removed += 1
    return puzzle

# ============================
#   HÀM HỖ TRỢ CHO STREAMLIT
# ============================

def empty_board(n):
    return [[0] * n for _ in range(n)]

def board_to_df(board):
    n = len(board)
    return pd.DataFrame(
        board,
        index=[f"R{i+1}" for i in range(n)],
        columns=[f"C{j+1}" for j in range(n)],
    )

def df_to_board(df):
    arr = df.to_numpy()
    n = arr.shape[0]
    board = [
        [
            int(arr[r, c]) if str(arr[r, c]).strip().isdigit() else 0
            for c in range(n)
        ]
        for r in range(n)
    ]
    return board

def check_current_answer(board, initial, n, box_size):
    """Trả về (ok, message). Chỉ check các ô do người chơi nhập (initial==0)."""
    for r in range(n):
        for c in range(n):
            if initial[r][c] == 0 and board[r][c] != 0:
                val = board[r][c]
                if not (1 <= val <= n):
                    return False, f"Số ở ô ({r+1},{c+1}) phải trong khoảng 1..{n}"
                # tạm xóa ô rồi kiểm tra
                tmp = board[r][c]
                board[r][c] = 0
                if not valid_in_board(board, n, box_size, r, c, val):
                    board[r][c] = tmp
                    return False, f"Số {val} tại ô ({r+1},{c+1}) đang bị trùng hàng/cột/ô con."
                board[r][c] = tmp
    return True, "✓ Đáp án hiện tại hợp lệ!"

# ============================
#      STREAMLIT APP
# ============================

st.set_page_config(
    page_title="Thuật giải Sudoku",
    page_icon="🧩",
    layout="wide"
)

st.title("🧩 Thuật giải game Sudoku (Streamlit)")
st.markdown(
    "Nhập đề Sudoku hoặc để hệ thống sinh ngẫu nhiên, sau đó bấm **Giải nhanh** hoặc **Kiểm tra đáp án**.  "
    "Dùng số `0` cho ô trống."
)

# Sidebar: lựa chọn cấu hình
st.sidebar.header("⚙️ Cấu hình")
size_option = st.sidebar.selectbox(
    "Kích thước lưới",
    options=[9, 16, 25],
    format_func=lambda x: f"{x} x {x}"
)
difficulty = st.sidebar.selectbox(
    "Mức độ (khi sinh đề ngẫu nhiên)",
    options=["Dễ", "Trung bình", "Khó"]
)
source = st.sidebar.radio(
    "Nguồn đề",
    options=["Tạo ngẫu nhiên", "Tự nhập thủ công", "Mở file CSV"]
)

uploaded_csv = None
if source == "Mở file CSV":
    uploaded_csv = st.sidebar.file_uploader(
        "Chọn file CSV (0 = ô trống)",
        type=["csv"]
    )

# Khởi tạo state
n = size_option
box_size = int(math.sqrt(n))
if "n" not in st.session_state or st.session_state["n"] != n:
    st.session_state["n"] = n
    st.session_state["initial"] = empty_board(n)
    st.session_state["board"] = empty_board(n)

initial = st.session_state["initial"]
board = st.session_state["board"]

# Nút thao tác
col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)

with col_btn1:
    if st.button("🎲 Tạo đề mới"):
        if source == "Tạo ngẫu nhiên":
            full = generate_full_board(n)
            puzzle = remove_cells_for_difficulty(full, difficulty)
            st.session_state["initial"] = [row[:] for row in puzzle]
            st.session_state["board"] = [row[:] for row in puzzle]
        elif source == "Tự nhập thủ công":
            st.session_state["initial"] = empty_board(n)
            st.session_state["board"] = empty_board(n)
        else:  # CSV
            if uploaded_csv is None:
                st.warning("Vui lòng chọn file CSV trước.")
            else:
                content = uploaded_csv.read().decode("utf-8")
                reader = csv.reader(io.StringIO(content))
                rows = []
                for row in reader:
                    if not any(cell.strip() for cell in row):
                        continue
                    tokens = [tok.strip() for tok in row if tok.strip() != ""]
                    rows.append([int(tok) for tok in tokens])
                if len(rows) != n or any(len(r) != n for r in rows):
                    st.error(f"File CSV phải là ma trận {n}x{n}.")
                else:
                    st.session_state["initial"] = [r[:] for r in rows]
                    st.session_state["board"] = [r[:] for r in rows]

with col_btn2:
    if st.button("✔ Kiểm tra đáp án"):
        current_board = [row[:] for row in st.session_state["board"]]
        ok, msg = check_current_answer(
            current_board,
            st.session_state["initial"],
            n,
            box_size,
        )
        if ok:
            st.success(msg)
        else:
            st.error(msg)

with col_btn3:
    if st.button("⚡ Giải nhanh"):
        current_board = [row[:] for row in st.session_state["board"]]
        solved = solve_backtrack(current_board, n, box_size)
        if solved:
            st.session_state["board"] = [row[:] for row in current_board]
            st.success("✓ Đã giải xong Sudoku!")
        else:
            st.error("Không thể giải được bài này.")

with col_btn4:
    if st.button("🔄 Reset về đề ban đầu"):
        st.session_state["board"] = [
            row[:] for row in st.session_state["initial"]
        ]
        st.info("Đã reset về đề ban đầu.")

st.markdown("---")

# Hiển thị board và cho phép chỉnh sửa
st.subheader("📋 Bảng Sudoku (sửa trực tiếp)")

df = board_to_df(st.session_state["board"])
edited_df = st.data_editor(
    df,
    use_container_width=True,
    num_rows="fixed",
    key="board_editor",
)

st.session_state["board"] = df_to_board(edited_df)

st.caption(
    "Mẹo: điền số 0 vào ô trống. Sau khi chỉnh sửa, bấm lại các nút ở trên để kiểm tra hoặc giải."
)
