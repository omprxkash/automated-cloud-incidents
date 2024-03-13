; bubble_sort.asm — allocate a 6-element heap array, fill, sort, print

.code
main:
  ; Allocate 24 bytes for 6 ints
  PUSH 24
  ALLOC
  STORE 0        ; local[0] = arr (base address)

  ; Fill array with [5, 3, 8, 1, 9, 2]
  LOAD 0
  PUSH 0
  PUSH 5
  ASTORE

  LOAD 0
  PUSH 1
  PUSH 3
  ASTORE

  LOAD 0
  PUSH 2
  PUSH 8
  ASTORE

  LOAD 0
  PUSH 3
  PUSH 1
  ASTORE

  LOAD 0
  PUSH 4
  PUSH 9
  ASTORE

  LOAD 0
  PUSH 5
  PUSH 2
  ASTORE

  ; n = 6, i = 0
  PUSH 6
  STORE 1        ; local[1] = n
  PUSH 0
  STORE 2        ; local[2] = i

outer_loop:
  LOAD 2
  LOAD 1
  PUSH 1
  ISUB           ; n - 1
  ILT            ; i < n-1?
  JFALSE done_sort

  PUSH 0
  STORE 3        ; local[3] = j = 0

inner_loop:
  LOAD 3
  LOAD 1
  LOAD 2
  ISUB
  PUSH 1
  ISUB           ; n - i - 1
  ILT            ; j < n-i-1?
  JFALSE next_i

  ; load arr[j] and arr[j+1] to compare
  LOAD 0
  LOAD 3
  ALOAD          ; arr[j]

  LOAD 0
  LOAD 3
  PUSH 1
  IADD
  ALOAD          ; arr[j+1]

  IGT            ; arr[j] > arr[j+1]?
  JFALSE no_swap

  ; tmp = arr[j]
  LOAD 0
  LOAD 3
  ALOAD
  STORE 4        ; local[4] = tmp

  ; arr[j] = arr[j+1]
  LOAD 0
  LOAD 3
  LOAD 0
  LOAD 3
  PUSH 1
  IADD
  ALOAD
  ASTORE

  ; arr[j+1] = tmp
  LOAD 0
  LOAD 3
  PUSH 1
  IADD
  LOAD 4
  ASTORE

no_swap:
  LOAD 3
  PUSH 1
  IADD
  STORE 3        ; j++
  JUMP inner_loop

next_i:
  LOAD 2
  PUSH 1
  IADD
  STORE 2        ; i++
  JUMP outer_loop

done_sort:
  ; --- print phase ---
  PUSH 0
  STORE 5        ; local[5] = k = 0

print_loop:
  LOAD 5
  LOAD 1
  ILT            ; k < n?
  JFALSE done_print

  LOAD 0
  LOAD 5
  ALOAD
  PRINT

  LOAD 5
  PUSH 1
  IADD
  STORE 5        ; k++
  JUMP print_loop

done_print:
  LOAD 0
  FREE
  HALT
