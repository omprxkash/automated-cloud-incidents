; factorial.asm — compute 10! iteratively and print the result

.code
main:
  PUSH 10
  CALL factorial
  PRINT
  HALT

; factorial(n) : expects n on the stack, leaves n! on the stack
factorial:
  STORE 0        ; local[0] = n
  PUSH 1
  STORE 1        ; local[1] = result = 1

loop:
  LOAD 0
  PUSH 1
  IGT            ; n > 1?
  JFALSE done

  LOAD 1
  LOAD 0
  IMUL           ; result * n
  STORE 1        ; result = result * n

  LOAD 0
  PUSH 1
  ISUB           ; n - 1
  STORE 0        ; n = n - 1

  JUMP loop

done:
  LOAD 1         ; return result         ; push result
  RET
