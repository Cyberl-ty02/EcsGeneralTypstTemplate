#import "template.typ": dissertation
#import "config.typ": config, abstract, acknowledgements, declaration

#show: dissertation.with(
  config: config,
  abstract: abstract,
  acknowledgements: acknowledgements,
  declaration: declaration,
  appendices: include "appendix.typ",
)

#include "chapters/introduction.typ"
#include "chapters/methodology.typ"
#include "chapters/conclusion.typ"
