; hello.asm — prints a greeting stored in the static data section

.data
  msg "Hello, Oracle VM!"

.code
main:
  PUSH msg       ; push the heap address of msg
  PRINTS         ; print the null-terminated string at that address
  HALT
