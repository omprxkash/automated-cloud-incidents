; fibonacci.asm — compute fib(10) = 55 recursively and print the result

.code
main:
  PUSH 10
  CALL fib
  PRINT
  HALT

; fib(n) : expects n on the stack, leaves fib(n) on the stack
fib:
  STORE 0        ; local[0] = n

  LOAD 0
  PUSH 2
  ILT            ; n < 2?
  JFALSE recurse

  LOAD 0         ; base case: return n (fib(0)=0, fib(1)=1)
  RET

recurse:
  LOAD 0
  PUSH 1
  ISUB           ; n - 1
  CALL fib       ; fib(n-1)
  STORE 1        ; local[1] = fib(n-1)

  LOAD 0
  PUSH 2
  ISUB           ; n - 2
  CALL fib       ; fib(n-2)  (result stays on stack)

  LOAD 1         ; fib(n-1)
  IADD           ; fib(n-1) + fib(n-2)
  RET
