	.text
.LC0:
	.string	"%d\n"
printint:
	pushq	%rbp
	movq	%rsp, %rbp
	subq	$16, %rsp
	movl	%edi, -4(%rbp)
	movl	-4(%rbp), %eax
	movl	%eax, %esi
	leaq	.LC0(%rip), %rdi
	movl	$0, %eax
	call	printf@PLT
	nop
	leave
	ret

	.comm	i,8,8
	.comm	j,8,8
	.comm	foo,8,8
	.comm	bar,8,8
	.text
	.globl	main
	.type	main, @function
main:
	pushq	%rbp
	movq	%rsp, %rbp
	movq	$6, %r8
	movq	%r8, i(%rip)
	movq	$12, %r8
	movq	%r8, j(%rip)
	movq	i(%rip), %r8
	movq	j(%rip), %r9
	cmpq	%r9, %r8
	jge	L1
	movq	i(%rip), %r8
	movq	%r8, %rdi
	call	printint
	jmp	L2
L1:
	movq	j(%rip), %r8
	movq	%r8, %rdi
	call	printint
L2:
	movq	$42, %r8
	movq	%r8, foo(%rip)
	movq	$24, %r8
	movq	%r8, bar(%rip)
	movq	i(%rip), %r8
	movq	j(%rip), %r9
	cmpq	%r9, %r8
	jne	L3
	movq	foo(%rip), %r8
	movq	%r8, %rdi
	call	printint
	jmp	L4
L3:
	movq	bar(%rip), %r8
	movq	%r8, %rdi
	call	printint
L4:
	movl $0, %eax
	popq	%rbp
	ret
