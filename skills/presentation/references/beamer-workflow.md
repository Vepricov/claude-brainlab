# Beamer Workflow

## Default workflow

1. Read the paper source before drafting slides.
2. Identify the minimal story for the target talk length.
3. Create a frame outline first.
4. Add figures and equations only after the frame purpose is clear.
5. Compile after each substantial edit batch.
6. Fix layout problems immediately.

## Story structure for theory-heavy talks

Use this default order unless the user asks otherwise:

1. Problem and why current methods fail
2. Main idea of the paper
3. Core construction or update rule
4. Main theorem or proof idea
5. Algorithmic instantiation
6. Results and practical takeaway

## Compile-and-check loop

After adding or revising frames, run a full compile and inspect the log.

Important warnings to treat as real failures:

- `Overfull \hbox`
- `Overfull \vbox`
- clipped figures
- equations extending beyond slide width
- unreadable font scaling
- frame titles colliding with content
- `Frame text is shrunk`

## Preferred fixes

Fix overflow in this order:

1. cut text
2. split the frame
3. simplify the equation or move detail to backup
4. widen the figure area or change column balance
5. reduce font size slightly, but only if readability remains strong

Do not keep a frame that technically compiles but looks cramped.

## Quality bar

A finished Beamer deck should satisfy all of the following:

- every frame has one clear takeaway
- no visible overflow or crowding
- figures are readable without zoom
- theory frames state the idea before notation details
- slides look visually consistent across the whole deck
