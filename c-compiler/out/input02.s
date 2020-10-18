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

	.comm	foo,8,8
	.comm	bar,8,8
	.text
	.globl	main
	.type	main, @function
main:
	pushq	%rbp
	movq	%rsp, %rbp
	movq	$123, %r8
	movq	%r8, foo(%rip)
	movq	$2, %r8
	movq	%r8, bar(%rip)
	movq	foo(%rip), %r8
	movq	%r8, %rdi
	call	printint
	movq	bar(%rip), %r8
	movq	%r8, %rdi
	call	printint
	movq	foo(%rip), %r8
	movq	$5, %r9
	addq	%r8, %r9
	movq	$6, %r8
	movq	$30, %r10
	imulq	%r8, %r10
	movq	bar(%rip), %r8
	movq	%r10, %rax
	cqo
	idivq	%r8
	movq	%rax, %r10
	subq	%r10, %r9
	movq	%r9, %rdi
	call	printint
	movl $0, %eax
	popq	%rbp
	ret
