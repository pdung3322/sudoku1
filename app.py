import streamlit as st
import math, random, csv, io
from copy import deepcopy

# ================== CẤU HÌNH & CSS ====================
st.set_page_config(page_title="Thuật giải Sudoku", layout="wide")

st.markdown("""
<style>
    body {
        background-color: #f0f4fa;
    }
    .title-main {
        text-align: center;
        font-size: 30px;
        font-weight: bold;
        color: #0b5394;
        margin-bottom: 10px;
    }
    .panel-start {
        background-color: #EAF6FF;
        padding: 25px;
        border-radius: 14px;
        width: 90%;
        margin: auto;
        margin-top: 15px;
        margin-bottom: 20px;
    }
    .note-text {
        text-align: center;
        font-size: 11px;
        color: #555;
    }
</style>
""", unsafe_allow_html=True)

# =============== THUẬT TOÁN SUDOKU ====================
def valid(board, n, box, r, c, num):
    for k in range(n):
        if board[r][k] == num:
            return False
        if board[k][c] == num:
            return False
    sr = r - r % box
    sc = c - c % box
    for i in range(box):
        for j in range(box):
            if board[sr+i][sc+j] == num:
                return False
    return True

def solve(board, n, box):
    for r in range(n):
        for c in range(n):
            if board[r][c] == 0:
                for num in range(1, n+1):
                    if valid(board, n, box, r, c, num):
                        board[r][c] = num
                        if solve(board, n, box):
                            return True
                        board[r][c] = 0
                return False
    return True

def generate_full_board(n):
    box = int(math.sqrt(n))
    board = [[0]*n for _ in range(n)]
    nums = list(range(1, n+1))

    def helper(pos=0):
        if pos == n*n:
            return True
        r, c = divmod(pos, n)
        random.shuffle(nums)
        for num in nums:
            if valid(board, n, box, r, c, num):
                board[r][c] = num
                if helper(pos+1):
                    return True
                board[r][c] = 0
        return False

    if not helper():
        raise RuntimeError("Không tạo được board hoàn chỉnh.")
    return board

def remove_cells(board, difficulty):
    n = len(board)
    total = n*n
    puzzle = [row[:] for row in board]

    if n == 9:
        if difficulty == "Dễ":
            remove = 40
        elif difficulty == "Trung bình":
            remove = 50
        else:
            remove = 60
    else:  # cho gọn, không làm 16x16,25x25 phức tạp
        remove = int(total * 0.6)

    cells = [(r, c) for r in range(n) for c in range(n)]
    random.shuffle(cells)
    for i, (r, c) in enumerate(cells):
        if i >= remove:
            break
        puzzle[r][c] = 0
    return puzzle

def empty_board(n):
    return [[0]*n for _ in range(n)]

def build_steps(initial_board, solved_board):
    """Tạo list bước điền số từ board ban đầu tới lời giải (không backtracking)."""
    n = len(initial_board)
    steps = []
    for r in range(n):
        for c in range(n):
            if initial_board[r][c] == 0:
                steps.append((r, c, solved_board[r][c]))
    return steps

# =============== STATE BAN ĐẦU ========================
if "started" not in st.session_state:
    st.session_state.started = False

if "message" not in st.session_state:
    st.session_state.message = ""
    st.session_state.message_type = "info"

# =============== HÀM TẠO ĐỀ ===========================
def init_puzzle():
    size_text = st.session_state.size_text
    level = st.session_state.level
    source = st.session_state.source

    n = int(size_text.split("x")[0])
    box = int(math.sqrt(n))

    if source == "Tạo ngẫu nhiên":
        full = generate_full_board(n)
        puzzle = remove_cells(full, level)
    elif source == "Tự nhập thủ công":
        full = None
        puzzle = empty_board(n)
    else:  # CSV
        csv_content = st.session_state.get("csv_content")
        if not csv_content:
            puzzle = empty_board(n)
            st.session_state.message = "⚠ Chưa chọn file CSV, tạo bảng trống."
            st.session_state.message_type = "warning"
        else:
            reader = csv.reader(io.StringIO(csv_content))
            rows = []
            for row in reader:
                if not any(cell.strip() for cell in row):
                    continue
                tokens = [tok.strip() for tok in row if tok.strip() != ""]
                rows.append([int(tok) for tok in tokens])
            if len(rows) == 0 or len(rows) != len(rows[0]):
                puzzle = empty_board(n)
                st.session_state.message = "⚠ File CSV phải là ma trận vuông, dùng 0 cho ô trống."
                st.session_state.message_type = "warning"
            else:
                n = len(rows)
                box = int(math.sqrt(n))
                puzzle = rows

    st.session_state.n = n
    st.session_state.box = box
    st.session_state.initial_board = [row[:] for row in puzzle]
    st.session_state.board = [row[:] for row in puzzle]

    # Clear widget state của từng ô nếu có
    for r in range(n):
        for c in range(n):
            key = f"cell_{r}_{c}"
            if key in st.session_state:
                del st.session_state[key]

# =============== CALLBACK BUTTONS ======================
def cb_go_start():
    st.session_state.started = False
    st.session_state.message = ""
    st.session_state.message_type = "info"

def cb_reset():
    n = st.session_state.n
    initial = st.session_state.initial_board
    st.session_state.board = [row[:] for row in initial]
    # Reset text_input value
    for r in range(n):
        for c in range(n):
            key = f"cell_{r}_{c}"
            if key in st.session_state:
                st.session_state[key] = "" if initial[r][c] == 0 else str(initial[r][c])
    st.session_state.message = "Đã reset về đề ban đầu."
    st.session_state.message_type = "success"

def cb_check():
    n = st.session_state.n
    box = st.session_state.box
    initial = st.session_state.initial_board
    board = st.session_state.board

    # kiểm tra từng ô người chơi nhập
    for r in range(n):
        for c in range(n):
            if board[r][c] == 0:
                st.session_state.message = "⚠ Bạn chưa điền hết các ô."
                st.session_state.message_type = "warning"
                return
            if not (1 <= board[r][c] <= n):
                st.session_state.message = f"Số ở ô ({r+1},{c+1}) phải trong khoảng 1..{n}."
                st.session_state.message_type = "error"
                return
            # kiểm tra trùng (bỏ qua chính nó)
            tmp = board[r][c]
            board[r][c] = 0
            if not valid(board, n, box, r, c, tmp):
                board[r][c] = tmp
                st.session_state.message = f"Số {tmp} tại ô ({r+1},{c+1}) bị trùng hàng/cột/ô con."
                st.session_state.message_type = "error"
                return
            board[r][c] = tmp

    st.session_state.message = "✓ Đáp án hiện tại hợp lệ!"
    st.session_state.message_type = "success"

def cb_solve_quick():
    n = st.session_state.n
    box = st.session_state.box
    board = deepcopy(st.session_state.board)
    if solve(board, n, box):
        st.session_state.board = [row[:] for row in board]
        # update widget value
        for r in range(n):
            for c in range(n):
                key = f"cell_{r}_{c}"
                val = board[r][c]
                st.session_state[key] = "" if val == 0 else str(val)
        st.session_state.message = "✓ Đã giải xong Sudoku!"
        st.session_state.message_type = "success"
    else:
        st.session_state.message = "✖ Không thể giải được bài này."
        st.session_state.message_type = "error"

def cb_view_steps():
    """Sinh danh sách bước giải để hiển thị (không animation phức tạp)."""
    n = st.session_state.n
    box = st.session_state.box
    init_b = st.session_state.initial_board
    board = deepcopy(init_b)

    if solve(board, n, box):
        steps = build_steps(init_b, board)
        st.session_state.solved_board = board
        st.session_state.steps = steps
        st.session_state.show_steps = True
        st.session_state.message = "Đã sinh quá trình giải, xem ở phần 'Quá trình giải' phía dưới."
        st.session_state.message_type = "info"
    else:
        st.session_state.message = "✖ Không thể giải được bài này."
        st.session_state.message_type = "error"

# ================== MÀN HÌNH CHỌN ĐỀ ==================
if not st.session_state.started:
    st.markdown("<div class='title-main'>Thuật giải game Sudoku</div>", unsafe_allow_html=True)

    with st.container():
        st.markdown("<div class='panel-start'>", unsafe_allow_html=True)
        col_left, col_mid, col_right = st.columns([1, 2, 1])

        with col_mid:
            size_text = st.selectbox("Chọn kích thước:", ["9x9"], index=0)
            level = st.selectbox("Chọn mức độ:", ["Dễ", "Trung bình", "Khó"], index=1)
            source = st.selectbox("Nguồn đề:", ["Tạo ngẫu nhiên", "Tự nhập thủ công", "Mở file CSV"])

            csv_file = None
            csv_content = None
            if source == "Mở file CSV":
                csv_file = st.file_uploader("Chọn file CSV (0 = ô trống)", type=["csv"])
                if csv_file is not None:
                    csv_content = csv_file.getvalue().decode("utf-8")

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        "<p class='note-text'>Ghi chú: CSV định dạng mỗi hàng một dòng, phân tách bằng dấu phẩy. 0 = ô trống.</p>",
        unsafe_allow_html=True
    )

    if st.button("Bắt đầu", type="primary"):
        st.session_state.started = True
        st.session_state.size_text = size_text
        st.session_state.level = level
        st.session_state.source = source
        st.session_state.csv_content = csv_content
        st.session_state.show_steps = False
        init_puzzle()
        st.experimental_rerun()

    st.stop()

# ================== MÀN HÌNH GIẢI SUDOKU ==================
n = st.session_state.n
box = st.session_state.box
board = st.session_state.board
initial = st.session_state.initial_board

st.markdown("<div class='title-main'>Thuật giải game Sudoku</div>", unsafe_allow_html=True)

# Hai cột: bảng & panel điều khiển
col_board, col_ctrl = st.columns([3, 1])

# -------- BẢNG SUDOKU (giữa màn hình) --------------
with col_board:
    st.write("")  # spacing
    new_board = [[0]*n for _ in range(n)]

    for r in range(n):
        row_cols = st.columns(n)
        for c in range(n):
            key = f"cell_{r}_{c}"
            val = board[r][c]
            default_str = "" if val == 0 else str(val)

            # lần đầu tạo ô -> set default vào session_state
            if key not in st.session_state:
                st.session_state[key] = default_str

            disabled = initial[r][c] != 0
            out = row_cols[c].text_input(
                "",
                max_chars=1,
                key=key,
                disabled=disabled
            )

            # lấy giá trị người dùng nhập (trong session_state[key])
            v = st.session_state[key]
            new_board[r][c] = int(v) if str(v).isdigit() else 0

    # cập nhật lại board theo giá trị nhập
    st.session_state.board = [row[:] for row in new_board]

# -------- PANEL ĐIỀU KHIỂN (bên phải) --------------
with col_ctrl:
    st.write("")
    st.button("Chọn đề bài (mở CSV hoặc nhập mới)", use_container_width=True, on_click=cb_go_start)
    st.button("Kiểm tra đáp án", use_container_width=True, on_click=cb_check)
    st.button("Xem quá trình giải", use_container_width=True, on_click=cb_view_steps)
    st.button("Giải nhanh", use_container_width=True, on_click=cb_solve_quick)
    st.button("Reset", use_container_width=True, on_click=cb_reset)

    st.markdown("**Tốc độ giải (delay bước)**")
    st.radio(
        "",
        ["Nhanh", "Trung bình", "Chậm"],
        index=1,
        horizontal=True,
        key="speed_choice"
    )

# -------- HIỂN THỊ THÔNG BÁO ------------------------
if st.session_state.message:
    if st.session_state.message_type == "success":
        st.success(st.session_state.message)
    elif st.session_state.message_type == "warning":
        st.warning(st.session_state.message)
    elif st.session_state.message_type == "error":
        st.error(st.session_state.message)
    else:
        st.info(st.session_state.message)

# -------- QUÁ TRÌNH GIẢI (DẠNG LIST BƯỚC) ----------
if st.session_state.get("show_steps", False):
    steps = st.session_state.get("steps", [])
    if steps:
        with st.expander("Quá trình giải (điền từng ô)", expanded=False):
            for i, (r, c, v) in enumerate(steps, start=1):
                st.write(f"Bước {i}: điền **{v}** vào ô hàng {r+1}, cột {c+1}")
