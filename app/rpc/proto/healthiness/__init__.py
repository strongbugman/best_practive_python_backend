# Generated by the protocol buffer compiler.  DO NOT EDIT!
# sources: app/rpc/healthiness.proto
# plugin: python-betterproto
from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, Optional

import betterproto
import grpclib
from betterproto.grpc.grpclib_server import ServiceBase

if TYPE_CHECKING:
    import grpclib.server
    from betterproto.grpc.grpclib_client import MetadataLike
    from grpclib.metadata import Deadline


@dataclass(eq=False, repr=False)
class CheckRequest(betterproto.Message):
    message: str = betterproto.string_field(1)


@dataclass(eq=False, repr=False)
class CheckResponse(betterproto.Message):
    message: str = betterproto.string_field(1)


class HealthinessStub(betterproto.ServiceStub):
    async def check(
        self,
        check_request: "CheckRequest",
        *,
        timeout: Optional[float] = None,
        deadline: Optional["Deadline"] = None,
        metadata: Optional["MetadataLike"] = None
    ) -> "CheckResponse":
        return await self._unary_unary(
            "/healthiness.Healthiness/Check",
            check_request,
            CheckResponse,
            timeout=timeout,
            deadline=deadline,
            metadata=metadata,
        )


class HealthinessBase(ServiceBase):
    async def check(self, check_request: "CheckRequest") -> "CheckResponse":
        raise grpclib.GRPCError(grpclib.const.Status.UNIMPLEMENTED)

    async def __rpc_check(
        self, stream: "grpclib.server.Stream[CheckRequest, CheckResponse]"
    ) -> None:
        request = await stream.recv_message()
        response = await self.check(request)
        await stream.send_message(response)

    def __mapping__(self) -> Dict[str, grpclib.const.Handler]:
        return {
            "/healthiness.Healthiness/Check": grpclib.const.Handler(
                self.__rpc_check,
                grpclib.const.Cardinality.UNARY_UNARY,
                CheckRequest,
                CheckResponse,
            ),
        }